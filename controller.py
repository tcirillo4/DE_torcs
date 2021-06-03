#!/usr/bin/python
import sys
import math
import snakeoil
from threading import Thread
import subprocess
import time
import json
import os
import shutil


class Track():

    def __init__(self):
        self.laplength= 0 
        self.width= 0 
        self.sectionList= list() 
        self.usable_model= False 

    def __repr__(self):
        o= 'TrackList:\n'
        o+= '\n'.join([repr(x) for x in self.sectionList])
        o+= "\nLap Length: %s\n" % self.laplength
        return o

    def post_process_track(self):
        ws= [round(s.width) for s in self.sectionList]
        ws= filter(lambda O:O,ws) 
        ws.sort()          
        self.width= ws[len(ws)/2]   
        cleanedlist= list()
        TooShortToBeASect= 6
        for n,s in enumerate(self.sectionList):
            if s.dist > TooShortToBeASect:  
                if cleanedlist and not s.direction and not cleanedlist[-1].direction:
                    cleanedlist[-1].end= s.end
                else:
                    cleanedlist.append(s)
            else:
                if cleanedlist: 
                    prevS= cleanedlist[-1] 
                    prevS.end= s.apex 
                    prevS.dist= prevS.end-prevS.start
                    prevS.apex= prevS.dist/2 + prevS.start
                if len(self.sectionList)-1 >= n+1: 
                    nextS= self.sectionList[n+1]
                    nextS.start= s.apex 
                    nextS.dist= nextS.end-nextS.start  
                    nextS.apex= nextS.dist/2 + nextS.start
                else: 
                    prevS.end= self.laplength  
                    prevS.dist= prevS.end-prevS.start
                    prevS.apex= prevS.dist/2 + prevS.start
        self.sectionList= cleanedlist
        self.usable_model= True 

    def write_track(self,fn):
        firstline= "%f\n" % self.width 
        f= open(fn+'.trackinfo','w')
        f.write(firstline)
        for s in self.sectionList:
            ts= '%f %f %f %d\n' % (s.start,s.end,s.magnitude,s.self.badness)
            f.write(ts)
        f.close()

    def load_track(self,fn):
        self.sectionList= list() 
        with open(fn+'.trackinfo','r') as f:
            self.width= float(f.readline().strip())
            for l in f:
                data=l.strip().split(' ') 
                TS= TrackSection(float(data[0]),float(data[1]),float(data[2]),self.width,int(data[3]))
                self.sectionList.append(TS)
        self.laplength= self.sectionList[-1].end
        self.usable_model= True 
        
    def section_in_now(self,d):
        for s in self.sectionList:
            if s.start < d < s.end:
                return s
        else:
            return None

    def section_ahead(self,d):
        for n,s in enumerate(self.sectionList):
            if s.start < d < s.end:
                if n < len(self.sectionList)-1:
                    return self.sectionList[n+1]
                else: 
                    return self.sectionList[0]
        else:
            return None

    def record_badness(self,b,d):
        sn= self.section_in_now(d)
        if sn:
            sn.self.badness+= b

class TrackSection():

    def __init__(self,sBegin,sEnd,sMag,sWidth,sBadness):
        if sMag:
            self.direction= int(abs(sMag)/sMag) 
        else:
            self.direction= 0 
        self.start= sBegin 
        self.end= sEnd     
        self.dist= self.end-self.start
        if not self.dist: self.dist= .1 
        self.apex= self.start + self.dist/2 
        self.magnitude= sMag 
        self.width= sWidth 
        self.severity= self.magnitude/self.dist 
        self.badness= sBadness

    def __repr__(self):
        tt= ['Right', 'Straight', 'Left'][self.direction+1]
        o=  "S: %f  " % self.start
        o+= "E: %f  " % self.end
        o+= "L: %f  " % (self.end-self.start)
        o+= "Type: %s  " % tt
        o+= "M: %f " % self.magnitude
        o+= "B: %f " % self.badness
        return o

    def update(self, distFromStart, trackPos, steer, angle, z):
        pass

    def current_section(self,x):
        return self.begin <= x and x <= self.end


class Controller():

    def init(self, idx, parameters):
        self.target_speed= 0 
        self.lap= 0 
        self.prev_distance_from_start= 1 
        self.learn_final= False 
        self.opHistory= list() 
        self.trackHistory= [0] 
        self.TRACKHISTORYMAX= 50 
        self.secType= 0 
        self.secBegin= 0 
        self.secMagnitude= 0 
        self.secWidth= 0 
        self.sangs= [-45,-19,-12,-7,-4,-2.5,-1.7,-1,-.5,0,.5,1,1.7,2.5,4,7,12,19,45]
        self.sangsrad= [(math.pi*X/180.0) for X in self.sangs]
        self.badness= 0
        self.T= Track()
        self.C= snakeoil.Client(parameters=parameters, port=3001 + (idx - 1))

    def automatic_transimission(self,P,r,g,c,rpm,sx,ts,tick):
        clutch_releaseF= .05 
        ng,nc= g,c 
        if ts < 0 and g > -1: 
            ng= -1
            nc= 1
        elif ts>0 and g<0:
            ng= g+1
            nc= 1
        elif c > 0:
            if g: 
                nc= c - clutch_releaseF 
            else: 
                if ts < 0:
                    ng= -1 
                else:
                    ng= 1 
        elif not tick % 50 and sx > 20:
            pass 
        elif g==6 and rpm<P['dnsh5rpm']: 
            ng= g-1 
            nc= 1
        elif g==5 and rpm<P['dnsh4rpm']: 
            ng= g-1 
            nc= 1
        elif g==4 and rpm<P['dnsh3rpm']:
            ng= g-1 
            nc= 1
        elif g==3 and rpm<P['dnsh2rpm']:
            ng= g-1 
            nc= 1
        elif g==2 and rpm<P['dnsh1rpm']:
            ng= g-1 
            nc= 1
        elif g==5 and rpm>P['upsh6rpm']: 
            ng= g+1
            nc= 1
        elif g==4 and rpm>P['upsh5rpm']: 
            ng= g+1
            nc= 1
        elif g==3 and rpm>P['upsh4rpm']: 
            ng= g+1
            nc= 1
        elif g==2 and rpm>P['upsh3rpm']: 
            ng= g+1
            nc= 1
        elif g==1 and rpm>P['upsh2rpm']: 
            ng= g+1
            nc= 1
        elif not g:
            ng= 1
            nc= 1
        else:
            pass
        return ng,nc

    def find_slip(self,wsv_list):
        w1,w2,w3,w4= wsv_list
        if w1:
            slip= (w3+w4) - (w1+w2)
        else:
            slip= 0
        return slip

    def track_sensor_analysis(self,t,a):
        alpha= 0
        sense= 1 
        farthest= None,None 
        ps= list()
        realt= list()
        self.sangsradang= [(math.pi*X/180.0)+a for X in self.sangs] 
        for n,sang in enumerate(self.sangsradang):
            x,y= t[n]*math.cos(sang),t[n]*-math.sin(sang)
            if float(x) > 190:
                alpha= math.pi
            else:
                ps.append((x,y))
                realt.append(t[n])
        firstYs= [ p[1] for p in ps[0:3] ]
        lastYs= [ p[1] for p in ps[-3:] ]
        straightnessf= abs(1- abs(min(firstYs))/max(.0001,abs(max(firstYs))))
        straightnessl= abs(1- abs(min(lastYs))/max(.0001,abs(max(lastYs))))
        straightness= max(straightnessl,straightnessf)
        farthest= realt.index(max(realt))
        ls= ps[0:farthest] 
        rs= ps[farthest+1:] 
        rs.reverse() 
        if farthest > 0 and farthest < len(ps)-1: 
            beforePdist= t[farthest-1]
            afterPdist=  t[farthest+1]
            if beforePdist > afterPdist: 
                sense= -1
                outsideset= ls
                insideset= rs
                ls.append(ps[farthest]) 
            else:                        
                outsideset= rs
                insideset= ls
                rs.append(ps[farthest]) 
        else: 
            if ps[0][0] > ps[-1][0]: 
                ps.reverse()
                farthest= (len(ps)-1) - farthest 
            if ps[0][1] > ps[-1][1]: 
                sense= -1
                outsideset= ls
                insideset= rs
            else: 
                outsideset= rs
                insideset= ls
        maxpdist= 0
        if not outsideset:
            return (0,a,2)
        nearx,neary= outsideset[0][0],outsideset[0][1]
        farx,fary= outsideset[-1][0],outsideset[-1][1]
        cdeltax,cdeltay= (farx-nearx),(fary-neary)
        c= math.sqrt(cdeltax*cdeltax + cdeltay*cdeltay)
        for p in outsideset[1:-1]: 
            dx1= p[0] - nearx
            dy1= p[1] - neary
            dx2= p[0] - farx
            dy2= p[1] - fary
            a= math.sqrt(dx1*dx1+dy1*dy1)
            b= math.sqrt(dx2*dx2+dy2*dy2)
            pdistances= a + b
            if pdistances > maxpdist:
                maxpdist= pdistances
                inflectionp= p  
                ia= a 
                ib= b 
        if maxpdist and not alpha:
            infleX= inflectionp[0]
            preprealpha= 2*ia*ib
            if not preprealpha: preprealpha= .00000001 
            prealpha= (ia*ia+ib*ib-c*c)/preprealpha
            if prealpha > 1: alpha= 0
            elif prealpha < -1: alpha= math.pi
            else:
                alpha= math.acos(prealpha)
            turnsangle= sense*(180-(alpha *180 / math.pi))
        else:
            infleX= max(t)
            turnsangle= self.sangs[t.index(infleX)]
        return (infleX,turnsangle,straightness)

    def speed_planning(self, P,d,t,tp,sx,sy,st,a,infleX,infleA):
        cansee= max(t[2:17])
        if cansee > 0:
            carmax= P['carmaxvisib'] * cansee 
        else:
            carmax= 69
        if cansee <0: 
            return P['backontracksx'] 
        if cansee > 190 and abs(a)<.1:
            return carmax 
        if t[9] < 40:  
            return P['obviousbase'] + t[9] * P['obvious']
        if infleA:
            willneedtobegoing= 600-180.0*math.log(abs(infleA))
            willneedtobegoing= max(willneedtobegoing,P['carmin']) 
        else: 
            willneedtobegoing= carmax
        brakingpacecut= 150 
        if sx > brakingpacecut:
            brakingpace= P['brakingpacefast']
        else:
            brakingpace= P['brakingpaceslow']
        base= min(infleX * brakingpace + willneedtobegoing,carmax)
        base= max(base,P['carmin']) 
        if st<P['consideredstr8']: 
            return base
        uncoolsy= abs(sy)/sx
        syadjust= 2 - 1 / P['oksyp'] * uncoolsy
        return base * syadjust 

    def damage_speed_adjustment(self, d):
        dsa= 1
        if d > 1000: dsa=.98
        if d > 2000: dsa=.96
        if d > 3000: dsa=.94
        if d > 4000: dsa=.92
        if d > 5000: dsa=.90
        if d > 6000: dsa=.88
        return dsa

    def jump_speed_adjustment(self, z):
        offtheground= snakeoil.clip(z-.350,0,1000)
        jsa= offtheground * -800
        return jsa

    def traffic_speed_adjustment(self, os,sx,ts,tsen):
        if not self.opHistory: 
            self.opHistory= os 
            return 0 
        tsa= 0 
        mpn= 0 
        sn=  min(os[17],os[18])  
        if sn > tsen[9] and tsen[9]>0: 
            return 0                   
        if sn < 15:
            sn=  min(sn , os[16],os[19])  
        if sn < 8:
            sn=  min(sn , os[15],os[20])  
        sn-= 5 
        if sn<3: 
            self.opHistory= os 
            return -ts 
        opn= mpn+sn 
        mpp= mpn - sx/180 
        sp= min(self.opHistory[17],self.opHistory[18]) 
        if sp < 15:
            sp=  min(sp , os[16],os[19])  
        if sp < 8:
            sp=  min(sn , os[15],os[20])  
        sp-= 5 
        self.opHistory= os 
        opp= mpp+sp 
        osx= (opn-opp) * 180 
        osx= snakeoil.clip(osx,0,300) 
        if osx-sx > 0: return 0 
        max_tsa= osx - ts 
        max_worry= 80 
        full_serious= 20 
        if sn > max_worry:
            seriousness= 0
        elif sn < full_serious:
            seriousness= 1
        else:
            seriousness= (max_worry-sn)/(max_worry-full_serious)
        tsa= max_tsa * seriousness
        tsa= snakeoil.clip(tsa,-ts,0) 
        return tsa

    def steer_centeralign(self, P,sti,tp,a,ttp=0):
        pointing_ahead= abs(a) < P['pointingahead'] 
        onthetrack= abs(tp) < P['sortofontrack']
        offrd= 1
        if not onthetrack:
            offrd= P['offroad']
        if pointing_ahead:
            sto= a 
        else:
            sto= a * P['backward']
        ttp*= 1-a  
        sto+= (ttp - min(tp,P['steer2edge'])) * P['s2cen'] * offrd 
        return sto 

    def speed_appropriate_steer(self, P,sto,sx):
        if sx > 0:
            stmax=  max(P['sxappropriatest1']/math.sqrt(sx)-P['sxappropriatest2'],P['safeatanyspeed'])
        else:
            stmax= 1
        return snakeoil.clip(sto,-stmax,stmax)

    def steer_reactive(self, P,sti,tp,a,t,sx,infleX,infleA,str8ness):
        if abs(a) > .6: 
            return self.steer_centeralign(P,sti,tp,a)
        maxsen= max(t)
        ttp= 0
        aadj= a
        if maxsen > 0 and abs(tp) < .99:
            MaxSensorPos= t.index(maxsen)
            MaxSensorAng= self.sangsrad[MaxSensorPos]
            sensangF= -.9  
            aadj= MaxSensorAng * sensangF
            if maxsen < 40:
                ttp= MaxSensorAng * - P['s2sen'] / maxsen
            else: 
                if str8ness < P['str8thresh'] and abs(infleA)>P['ignoreinfleA']:
                    try:
                        ttp= -abs(infleA)/infleA
                    except ZeroDivisionError:
                        ttp = 0
                    aadj= 0 
                else:
                    ttp= 0
            senslimF= .031 
            ttp= snakeoil.clip(ttp,tp-senslimF,tp+senslimF)
        else: 
            aadj= a
            if tp:
                ttp= .94 * abs(tp) / tp
            else:
                ttp= 0
        sto= self.steer_centeralign(P,sti,tp,aadj,ttp)
        return self.speed_appropriate_steer(P,sto,sx)

    def traffic_navigation(self, os, sti):
        sto= sti 
        c= min(os[4:32]) 
        cs= os.index(c)  
        if not c: c= .0001
        if min(os[18:26])<7:
            sto+= .5/c
        if min(os[8:17])<7:
            sto-= .5/c
        if cs == 17:
            sto+= .1/c
        if cs == 18:
            sto-= .1/c
        if .1 < os[17] < 40:
            sto+= .01
        if .1 < os[18] < 40:
            sto-= .01
        return sto

    def clutch_control(self, P,cli,sl,sx,sy,g):
        if abs(sx) < .1 and not cli: 
            return 1  
        clo= cli-.2 
        clo+= sl/P['clutchslip']
        clo+= sy/P['clutchspin']
        return clo

    def throttle_control(self, P,ai,ts,sx,sl,sy,ang,steer):
        ao= ai 
        if ts < 0:
            tooslow= sx-ts 
        else:
            okmaxspeed4steer= P['stst']*steer*steer-P['st']*steer+P['stC']
            if steer> P['fullstis']:
                ts=P['fullstmaxsx']
            else:
                ts= min(ts,okmaxspeed4steer)
            tooslow= ts-sx 
        ao= 2 / (1+math.exp(-tooslow)) -1
        ao-= abs(sl) * P['slipdec'] 
        spincut= P['spincutint']-P['spincutslp']*abs(sy)
        spincut= snakeoil.clip(spincut,P['spincutclip'],1)
        ao*= spincut
        ww= abs(ang)/P['wwlim']
        wwcut=  min(ww,.1)
        if ts>0 and sx >5:
            ao-= wwcut
        if ao > .8: ao= 1
        return ao
        
    def brake_control(self, P,bi,sx,sy,ts,sk):
        bo= bi 
        toofast= sx-ts
        if toofast < 0: 
            return 0
        if toofast: 
            #bo+= P['brake'] * toofast / max(1,abs(sk))
            bo=1
        if sk > P['seriousABS']: bo=0 
        if sx < 0: bo= 0 
        if sx < -.1 and ts > 0:  
            bo+= .05
        sycon= 1
        if sy:
            sycon= min(1,  P['sycon2']-P['sycon1']*math.log(abs(sy))  )
        return min(bo,sycon)

    def iberian_skid(self,wsv,sx):
        speedps= sx/3.6
        sxshouldbe= sum( [ [.3179,.3179,.3276,.3276][x] * wsv[x] for x in range(3) ] ) / 4.0
        return speedps-sxshouldbe

    def skid_severity(self,P,wsv_list,sx):
        skid= 0
        avgws= sum(wsv_list)/4 
        if avgws:
            skid= P['skidsev1']*sx/avgws - P['wheeldia'] 
        return skid

    def car_might_be_stuck(self,sx,a,p):
        if p > 1.2 and a < -.5:
            return True
        if p < -1.2 and a > .5:
            return True
        if sx < 3: 
            return True
        return False 

    def car_is_stuck(self,sx,t,a,p,fwdtsen,ts):
        if fwdtsen > 5 and ts > 0: 
            return False
        if abs(a)<.5 and abs(p)<2 and ts > 0: 
            return False
        if t < 100: 
            return False
        return True

    def learn_track(self,st,a,t,dfs):
        NOSTEER= 0.07 
        self.T.laplength= max(dfs,self.T.laplength)
        if len(self.trackHistory) >= self.TRACKHISTORYMAX:
            self.trackHistory.pop(0) 
        self.trackHistory.append(st)
        steer_sma= sum(self.trackHistory)/len(self.trackHistory) 
        if abs(steer_sma) > NOSTEER: 
            self.secType_now= abs(steer_sma)/steer_sma
            if self.secType != self.secType_now: 
                self.T.sectionList.append( TrackSection(self.secBegin,dfs, self.secMagnitude, self.secWidth,0) )
                self.secMagnitude= 0 
                self.secWidth= 0 
                self.secType= self.secType_now 
                self.secBegin= dfs 
            self.secMagnitude+= st 
        else: 
            if self.secType: 
                self.T.sectionList.append( TrackSection(self.secBegin,dfs, self.secMagnitude, self.secWidth,0) )
                self.secMagnitude= 0 
                self.secWidth= 0 
                self.secType= 0 
                self.secBegin= dfs 
        if not self.secWidth and abs(a) < NOSTEER:
            self.secWidth= t[0]+t[-1] 
            
    def learn_track_final(self,dfs):
        self.T.sectionList.append( TrackSection(self.secBegin,dfs, self.secMagnitude, self.secWidth, self.badness) )

    def drive(self,tick):
        S,R,P= self.C.S.d,self.C.R.d,self.C.P
        self.badness= S['damage']-self.badness 
        skid= self.skid_severity(P,S['wheelSpinVel'],S['speedX'])
        if skid>1:
            self.badness+= 15
        if self.car_might_be_stuck(S['speedX'],S['angle'],S['trackPos']):
            S['stucktimer']= (S['stucktimer']%400) + 1
            if self.car_is_stuck(S['speedX'],S['stucktimer'],S['angle'],
                            S['trackPos'],S['track'][9],self.target_speed):
                self.badness+= 100
                R['brake']= 0 
                if self.target_speed > 0:
                    self.target_speed= -40
                else:
                    self.target_speed= 40
        else: 
            S['stucktimer']= 0
        if S['z']>4: 
            self.badness+= 20
        infleX,infleA,straightness= self.track_sensor_analysis(S['track'],S['angle'])
        if self.target_speed>0:
            if self.C.stage: 
                if not S['stucktimer']:
                    self.target_speed= self.speed_planning(P,S['distFromStart'],S['track'],S['trackPos'],
                                            S['speedX'],S['speedY'],R['steer'],S['angle'],
                                            infleX,infleA)
                self.target_speed+= self.jump_speed_adjustment(S['z'])
                if self.C.stage > 1: 
                    self.target_speed+= self.traffic_speed_adjustment(
                            S['opponents'],S['speedX'],self.target_speed,S['track'])
                self.target_speed*= self.damage_speed_adjustment(S['damage'])
            else:
                if self.lap > 1 and self.T.usable_model:
                    self.target_speed= self.speed_planning(P,S['distFromStart'],S['track'],S['trackPos'],
                                            S['speedX'],S['speedY'],R['steer'],S['angle'],
                                            infleX,infleA)
                    self.target_speed*= self.damage_speed_adjustment(S['damage'])
                else: 
                    self.target_speed= 50
        self.target_speed= min(self.target_speed,333)
        caution= 1 
        if self.T.usable_model:
            snow= self.T.section_in_now(S['distFromStart'])
            snext= self.T.section_ahead(S['distFromStart'])
            if snow:
                if snow.self.badness>100: caution= .80
                if snow.self.badness>1000: caution= .65
                if snow.self.badness>10000: caution= .4
                if snext:
                    if snow.end - S['distFromStart'] < 200: 
                        if snext.self.badness>100: caution= .90
                        if snext.self.badness>1000: caution= .75
                        if snext.self.badness>10000: caution= .5
        self.target_speed*= caution
        if self.T.usable_model or self.C.stage>1:
            if abs(S['trackPos']) > 1:
                s= self.steer_centeralign(P,R['steer'],S['trackPos'],S['angle'])
                self.badness+= 1
            else:
                s= self.steer_reactive(P,R['steer'],S['trackPos'],S['angle'],S['track'],
                                                    S['speedX'],infleX,infleA,straightness)
        else:
            s= self.steer_centeralign(P,R['steer'],S['trackPos'],S['angle'])
        R['steer']= s
        if S['stucktimer'] and S['distRaced']>20:
            if self.target_speed<0:
                R['steer']= -S['angle']
        if self.C.stage > 1: 
            if self.target_speed < 0: 
                self.target_speed*= snakeoil.clip(S['opponents'][0]/20,  .1, 1)
                self.target_speed*= snakeoil.clip(S['opponents'][35]/20, .1, 1)
            else:
                R['steer']= self.speed_appropriate_steer(P,
                        self.traffic_navigation(S['opponents'], R['steer']),
                        S['speedX']+50)
        if not S['stucktimer']:
            self.target_speed= abs(self.target_speed) 
        slip= self.find_slip(S['wheelSpinVel'])
        R['accel']= self.throttle_control(P,R['accel'],self.target_speed,S['speedX'],slip,
                                    S['speedY'],S['angle'],R['steer'])
        if R['accel'] < .01:
            R['brake']= self.brake_control(P,R['brake'],S['speedX'],S['speedY'],self.target_speed,skid)
        else:
            R['brake']= 0
        R['gear'],R['clutch']= self.automatic_transimission(P,
            S['rpm'],S['gear'],R['clutch'],S['rpm'],S['speedX'],self.target_speed,tick)
        R['clutch']= self.clutch_control(P,R['clutch'],slip,S['speedX'],S['speedY'],S['gear'])
        if S['distRaced'] < S['distFromStart']: 
            self.lap= 0
        if self.prev_distance_from_start > S['distFromStart'] and abs(S['angle'])<.1:
            self.lap+= 1
        self.prev_distance_from_start= S['distFromStart']
        if not self.lap: 
            self.T.laplength= max(S['distFromStart'],self.T.laplength)
        elif self.lap == 1 and not self.usable_model: 
            self.learn_track(R['steer'],S['angle'],S['track'],S['distFromStart'])
        elif self.C.stage == 3:
            pass 
        else: 
            if not self.learn_final: 
                self.learn_track_final(self.T.laplength)
                self.T.post_process_track()
                self.learn_final= True
            if self.T.laplength:
                self.properself.lap= S['distRaced']/self.T.laplength
            else:
                self.properself.lap= 0
            if self.C.stage == 0 and self.lap < 4: 
                self.T.record_self.badness(self.badness,S['distFromStart'])
        S['targetSpeed']= self.target_speed 
        self.target_speed= 70 
        self.badness= S['damage']
        return

    def initialize_car(self):
        R= self.C.R.d
        R['gear']= 1 
        R['steer']= 0 
        R['brake']= 1 
        R['clutch']= 1 
        R['accel']= .22 
        R['focus']= 0 
        self.C.respond_to_server() 

def launch_server(i = 1):
    subprocess.call([os.path.join('bat_files','server.bat'), str(i)])

def run_all(controller, parameters, idx , track = 'forza'):
    controller.init(idx, parameters)
    assert(track in ['forza', 'eTrack_3', 'cgTrack_2', 'wheel'])
    TORCS_PATH = os.path.join('TORCS', 'torcs_' + str(idx))
    os.remove(os.path.join(TORCS_PATH, 'config', 'raceman', 'quickrace.xml'))
    shutil.copy(os.path.join(TORCS_PATH, 'config', 'custom_races', track +  '.xml'),os.path.join(TORCS_PATH, 'config', 'raceman','quickrace.xml'))
    Thread(target= launch_server, args=[idx]).start()
    controller.initialize_car()
    controller.C.S.d['stucktimer']= 0
    controller.C.S.d['targetSpeed']= 0
    if controller.C.stage == 1 or controller.C.stage == 2:
        try:
            controller.T.load_track(controller.C.trackname)
        except:
            print("Could not load the track: %s" % controller.C.trackname)
            sys.exit()
        print("Track loaded!")
    try:
        track_pos = []
        for step in range(controller.C.maxSteps,0,-1):
            controller.C.get_servers_input()
            controller.drive(step)
            controller.C.respond_to_server()
            track_pos.append(controller.C.S.d['trackPos'])
            if not controller.C.is_connected():
                break
        if not controller.C.stage:  
            T.write_track(controller.C.trackname) 
        results = {
            'trackPos' : track_pos,
            'racePos' : controller.C.S.d['racePos'],
            'damage' : controller.C.S.d['damage'],
            'lapTime' : controller.C.S.d['curLapTime'],
            'distRaced' : controller.C.S.d['distRaced'],
            'laplength' : controller.T.laplength
        }
        controller.C.respond_to_server()
        controller.C.shutdown()
    except Exception as ex:
        print("Error: " + str(ex))
        return {
            'trackPos' : [100],
            'racePos' : 100,
            'damage' : 10000,
            'lapTime' : 1000,
            'distRaced' : 10,
            'error' : True,
            'laplength' : controller.T.laplength
        }
    return results
    
def run_graphic(parameters):
    global C, T
    T= Track()
    C= snakeoil.Client(parameters=parameters)
    controller = Controller()
    controller.initialize_car(C)
    C.S.d['stucktimer']= 0
    C.S.d['targetSpeed']= 0
    if C.stage == 1 or C.stage == 2:
        try:
            T.load_track(C.trackname)
        except:
            print("Could not load the track: %s" % C.trackname)
            sys.exit()
        print("Track loaded!")
    for step in range(C.maxSteps,0,-1):
        C.get_servers_input()
        controller.drive(C,step)
        C.respond_to_server()
        if not C.is_connected():
            break
    if not C.stage:  
        T.write_track(C.trackname) 
    results = {
        'racePos' : C.S.d['racePos'],
        'damage' : C.S.d['damage'],
        'self.lapTime' : C.S.d['curLapTime']
    }
    C.respond_to_server()
    C.shutdown()
    return results

def read_parameters(keys):
    import csv
    parameters = []
    with open('1_input.csv', mode='r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for i, row in enumerate(csv_reader):
                parameters.append(dict())
                for j,key in enumerate(keys):
                    parameters[-1][key] = float(row[j])
    return parameters

if __name__ == "__main__":
    DEFAULT_TRACKS = ('forza','eTrack_3','cgTrack_2','wheel')
    pfile= open(os.path.join('output_files','best_parameters.json'),'r')
    parameters= json.load(pfile)
    # for track in DEFAULT_TRACKS:
    #     print('TRACK: ' + track)
    #     print(run_all(parameters, 1, track))
    run_graphic(parameters)
    # for _ in range(100):
    #     key= random.choice(list(parameters.keys()))
    #     new_param = parameters.copy()
    #     new_param[key] += random.random() * parameters[key]
    #     start = time.time()
    #     run_all(new_param)
    #     print('Time: ' + str(round(time.time() - start,2)))


