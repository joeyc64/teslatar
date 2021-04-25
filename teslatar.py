#
# Teslatar 2.0
#
import teslapy # Tesla API with new multi-factor authentification
import sys, time, random, logging, requests
from datetime import datetime, date, timedelta

# 
username="username@gmail.com"    # Tesla username
password="teslapassword"   # Tesla password
home_latitute=48.141356 # configure home address - https://www.latlong.net/convert-address-to-lat-long.html
home_longitute=8.195409

#
nWallboxKW = 11 # kW max power of wallbox, change to your wallbox!
finishHour = 7 # hour when car MUST reach end of charge!

# Calcs hours left from now until finish time
# Parameters:   then (time in hour when must be finished)
# Return: float hours
def CalcTimeLeftToCharge( then ):
    now=float(datetime.now().strftime("%H"))+float(datetime.now().strftime("%M"))/60
    hoursLeft=0
    if( now>then ):
        hoursLeft=24-now+then
    else:
        hoursLeft=then-now
    return( hoursLeft )

#gets an Array of datetime and prices (here for testing only random)
def getHourlyPrices():
    aPrices=[]
    
    logging.info("Query aWATTar for new pricing...")
    r = requests.get('https://api.awattar.de/v1/marketdata')
    j = r.json()["data"]
    #print( j )
    for i in j:
        #print( i["start_timestamp"]/1000, i["marketprice"], time.ctime(i["start_timestamp"]/1000), round(i["marketprice"]/10*1.19,2) )
        dt = datetime.fromtimestamp(i["start_timestamp"]/1000)
        p = round(i["marketprice"]/10*1.19,2)   # convert from Eur/MWh to Cent/kWh plus 19% VAT
        logging.info( dt.strftime("%Y-%m-%d %H = ")+str(p) )
        aPrices.append([dt,p ])
    return aPrices

#checks if nowtime is in current pricearray
def isInsidePriceHour( aPrices ):
    found=False
    i=0
    dt=datetime.now()
    #dt=datetime(2019,4,3,11,59,59)
    oneHour=timedelta(hours=1)
    while i<len(aPrices):
        #print( aPrices[i][0], aPrices[i][1] )
        if( aPrices[i][0]<=dt and dt<aPrices[i][0]+oneHour ):
            found=True
            break
        i+=1
    return found

# basic vars
aChargeMode = []   # time until charge must be finished (-1=start immediate)
aPricesChosen = []

#logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)
logging.basicConfig(filename="file.log", format='%(asctime)s - %(message)s', level=logging.INFO)
logging.critical("Startup Tesla Avatar")
time.sleep(10)

logging.info("Opening connection to Tesla API...")
while True:
    try:
        tesla = teslapy.Tesla( email, password )
        tesla.fetch_token()
        break
    except:
        logging.error("...could not connect (yet), wait, then try again...", exc_info=True)
        time.sleep(60)

vehicles = tesla.vehicle_list()
nNumCars = 0
while nNumCars<len(vehicles):
    v = vehicles[nNumCars]
    logging.info("Car #%u VIN=%s Name=%s, State=%s", nNumCars+1, v["vin"], v["display_name"], v["state"] )
    nNumCars+=1
cntExceptions=0    

startHour = datetime.now().hour
aPrices=[]
oldPriceHour=-1
oldLenPrices=-1
timeToFull=[]
mode=[]
oldMode=[]
lastModeChange=[]
oldChargeLimitSoc=[]
i=0
while i<nNumCars:
    aChargeMode+=[finishHour]
    aPricesChosen+=[0]
    mode+=[0]
    oldMode+=[-1]
    lastModeChange+=[0]
    oldChargeLimitSoc+=[0]
    timeToFull+=[0]
    i+=1

while True:

    try:
        
        # new hour? then load new prices from aWATTar
        if oldPriceHour != datetime.now().hour:
            # get array with price for every hour in the future
            aPrices=getHourlyPrices()
            oldPriceHour = datetime.now().hour
         
        # update vehicle structure
        vehicles=tesla.vehicle_list()   # this command does not effect sleep mode of car
        #print( vehicles )
        # check every car
        nCar=0
        info=["state","position","charge mode","idle","charge state"]
        while nCar<nNumCars:
            #
            v = vehicles[nCar]
            #
            # check if inside a charge hour, if yes then prepare to charge
            if mode[nCar]==3 : # CHARGE
                # check if current hour is allowed to CHARGE
                if isInsidePriceHour(aPricesChosen[nCar]) :
                    # yes, allowed to charge, then go ONLINE
                    if v["state"]!="online":
                        logging.info("Time to charge, wake the car up")
                        v.sync_wake_up()
                        lastModeChange[nCar]=0
                
            # query Tesla API for "state"
            info[0]=v["state"]
            if v["state"]!="online":
                # car is not online - let it sleep
                logging.info("Car#%u state is '%s', mode=%u", nCar+1, v["state"], mode[nCar] )
                oldMode[nCar]=mode[nCar]
                lastModeChange[nCar]=0
                nCar+=1
                continue
                
            # car is online, check if vehicle mode didn't change for x cycles (15min)
            if mode[nCar]==3 and isInsidePriceHour(aPricesChosen[nCar]) : # charge hour? don't check for letting sleep
                lastModeChange[nCar]=0
            lastModeChange[nCar]+=1
            if lastModeChange[nCar]>15 :
                logging.info("Car#%u seems to be idle, do not poll data anymore -> bring to sleep", nCar+1 ) 
                if lastModeChange[nCar]>15+30:  # try 30min to let it sleep
                    logging.info("Car#%u doesn't go asleep, start polling again", nCar+1 ) 
                    lastModeChange[nCar]=0
                nCar+=1
                continue                
                
            # Car needs to be online for getting more data
            v = vehicles[nCar]
            if v["state"]!="online":
                v.sync_wake_up()
            vd = v.get_vehicle_data()  
            ds=vd["drive_state"] 
            if ds["shift_state"]!=None :    # if driving then reset test-for-sleep counter
                lastModeChange[nCar]=0   
                nCar+=1
                continue                
            lati=ds["latitude"] # get position of car
            longi=ds["longitude"]
            if int(lati*1000)!=int(home_latitute*1000) or int(longi*1000)!=int(home_longitute*1000) :
                # car is not at home charger position, ignore
                info[1]="anywhere"
                mode[nCar]=0
                if mode[nCar]!=oldMode[nCar] :
                    logging.info("Car #%u is not at charger position - ignore", nCar+1)
                    logging.info( "%u, %u, %u, %u", int(lati*1000), int(home_latitute*1000), int(longi*1000), int(home_longitute*1000) )
                oldMode[nCar]=mode[nCar]
                nCar+=1
                continue
            info[1]="@home"
            #
            cs=vd['charge_state']
            logging.debug("Loop car #%u, mode=%u", nCar+1, mode[nCar])
            #
            # general check if charge logic should NOT be activated
            #   if no charge schedule is set (owner wants to start NOW, let the car do its thing)
            #   if charge cable is not inserted
            if cs["scheduled_charging_start_time"]==None :
                # no charge schedule, let it charge
                info[2]="always"
                mode[nCar]=0
                if mode[nCar]!=oldMode[nCar] :
                    logging.info("Charge 'always' activated in car #%u", nCar+1)
            else:
                info[2]="aWATTar"
                if cs["charge_limit_soc"]==100 and \
                    cs["charging_state"]!="Charging" :
                    v.command('START_CHARGE')
                    info[2]="topup" # finish to 100% now
                    mode[nCar]=0
                    logging.info("CHARGE_LIMIT_SOC is 100 -> start charging now")
                if cs["battery_level"]<10 and \
                    cs["charging_state"]!="Charging" :
                    v.command('START_CHARGE')
                    info[2]="toolow" # always charge if SOC<10% 
                    mode[nCar]=0
                    logging.info("STATE_OF_CHARGE<10 -> too low -> start charging now")
            #if cs["charge_port_door_open"]==False and \
            #    cs["charge_port_latch"]!="Engaged" :
            if cs["charge_port_door_open"]==False:
                # no charge cable - reset everything 
                mode[nCar]=0
                if mode[nCar]!=oldMode[nCar] :
                    logging.info("Cable unplugged in car #%u", nCar+1) 
            if mode[nCar]==0 and cs["charge_port_door_open"]==True and \
                    cs["charge_port_latch"]=="Engaged" and \
                    cs["charge_limit_soc"]<100 and \
                    cs["scheduled_charging_start_time"]!=None : # is charging scheduled?
                    mode[nCar]=1 # I want to charge depending on aWATTar pricing until next morning
                    if mode[nCar]!=oldMode[nCar] :
                        logging.info("Cable inserted in car #%u", nCar+1) 
            if mode[nCar]==1 : # I_WANT_TO_CHARGE
                # check if charge is possible
                # only if current SOC is at least 10% lower then MAX_SOC
                if cs["charge_limit_soc"]-cs["battery_level"]<10 :
                    # SOC is too high, no charge
                    logging.info("SOC is high enough, no charging necessary")
                else:
                    # if still not charging then start charging again
                    if cs["charging_state"]!="Charging" :
                        v.command('START_CHARGE')
                        logging.info("send cmd: start charging")
                    else:
                        # now it's charging! 
                        # But wait a bit until charging on full power and give the car time to calculate 'time_to_full_charge'
                        timeToFull[nCar]=0
                        i=10
                        while( i>0 ):
                            if( cs["charger_power"]<(nWallboxKW-nWallboxKW/10) ) : # wait until on full power, so that extimated time is exact
                                logging.info("...charging but not on full power yet (%s) - waiting...", cs["charger_power"])
                            else:
                                if( timeToFull[nCar]!=0 and timeToFull[nCar]==cs["time_to_full_charge"] ): # is it stable (same for a period)
                                    break    
                                timeToFull[nCar] = cs["time_to_full_charge"]
                                logging.info("time_to_full_charge = %s",cs["time_to_full_charge"])   # 4.33 for 4h20m
                            time.sleep(10) 
                            vd = v.get_vehicle_data()
                            cs=vd["charge_state"]
                            i=i-1
                        # ok?
                        if( i>0 ):
                            logging.info("found time_to_full_charge = %s", timeToFull[nCar] )
                            mode[nCar]=2
                        else:
                            mode[nCar]=0; # reset because error, takes too long
                            logging.info("Error, try again")
                            
            if mode[nCar]==2 : # CALCULATE_CHARGE_HOURS
                logging.info("calculating charging hours...")
                # calc max allowed charge hours
                maxHoursCharging=0
                if( aChargeMode[nCar]==-1 ) : # start charging immediatly?
                    maxHoursCharging=timeToFull[nCar]
                else:
                    maxHoursCharging=CalcTimeLeftToCharge(aChargeMode[nCar])
                    if( maxHoursCharging<timeToFull[nCar] ):
                        maxHoursCharging=timeToFull[nCar]
                logging.info("= %s",maxHoursCharging)
                # aPrices are already loaded and updated every new hour!
                # just take the next hours until charge must be finished
                oldLenPrices=len(aPrices) # remember the current amount of hours/prices
                aPricesMaxHours=aPrices[:int(maxHoursCharging)+1]
                logging.info( "Hours taken into account:" )
                logging.info( aPricesMaxHours )
                # sort all for best prices
                aPricesSorted=sorted(aPricesMaxHours, key=lambda x:x[1])
                logging.info( "Hours sorted for price:" )
                logging.info( aPricesSorted )
                # just take the hours to fully charge
                aPricesChosen[nCar]=aPricesSorted[:int(timeToFull[nCar])+1]
                logging.info( "Hours chosen for charging:" )
                logging.info( aPricesChosen[nCar] )
                oldChargeLimitSoc[nCar]=cs["charge_limit_soc"]
                mode[nCar]=3 # start the CHARGE
            if mode[nCar]==3 : # CHARGE
                # check if there is an updated price-structure from aWATTar - coming at 2pm everyday for the next day -> longer array!
                if len(aPrices) > oldLenPrices :
                    logging.info( "Updated price structure! Recalculate charge hours." )
                    oldLenPrices = len(aPrices)
                    mode[nCar] = 2  # set to CALCULATE_CHARGE_HOURS
                # has the target charge limit been changed on the app in the meantime (maybe from 80% to 90%)? Then recalculate charge hours
                if oldChargeLimitSoc[nCar] != cs["charge_limit_soc"] and \
                    cs["charge_limit_soc"]<100 :
                    logging.info( "CHARGE_LIMIT_SOC changed, recalculate charge times" )
                    mode[nCar] = 1  # set to I_WANT_TO_CHARGE	
                # check if current hour is allowed to CHARGE
                if isInsidePriceHour(aPricesChosen[nCar]) :
                    # yes, allowed to charge
                    if cs["charging_state"]!="Charging" :
                        if cs["battery_level"]<cs["charge_limit_soc"] : # only start charging if SOC is below MAX
                            v.command('START_CHARGE')
                            logging.info("Start charging command")
                        else: # is at max, so it's finished, stop the CHARGE logic
                            logging.info("Charge finished")
                            mode[nCar]=0   # reset logic
                else:
                    # no, not allowed to charge 
                    if cs["charging_state"]=="Charging" :
                        v.command('STOP_CHARGE')
                        logging.info("Stop charging command")
            #
            # info=["state","position","charge mode","ctrl-mode","charge state"]
            info[3]="inactive"
            if mode[nCar]==3:
                info[3]="active"
            info[4]=cs["charging_state"]
            if info[4]=="Charging":
                info[4]+="["+str(cs["battery_level"])+"%]"
            logging.info( "Car#%1u  STATE=%s  CHARGE=%s  CTRL-MODE=%s  STATE=%s", nCar+1, info[0], info[2], info[3], info[4] )
            oldMode[nCar]=mode[nCar]
            nCar+=1
        #
        logging.info("**")
        time.sleep(60)
    except :
        # exceptions happen all the time when Tesla server are busy, so no big deal, just wait a while and try again
        cntExceptions+=1
        logging.error("******EXCEPTION #%u", cntExceptions )
        logging.error( "%s, %s", sys.exc_info()[0], sys.exc_info()[1] )
        time.sleep(15)
        logging.info("RE-Opening connection to Tesla API...")
        while True:
            try:
                tesla = teslapy.Tesla( email, password )
                tesla.fetch_token()           
                time.sleep(30)
                break
            except:
                logging.error("...could not connect (yet), wait, then try again...", exc_info=True)
                time.sleep(60)
        
