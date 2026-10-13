* VERSIE Start 03/02/2020
* Dr. R. BEUNIS
* Segreg simulatie programma versie VFP 9.0

&& Gebruik van RAND(-1) (neemt seed van de klok) geeft identieke waarden
&& als de volgende RAND(-1)'s zo snel volgen dat de klokwaarde nog niet veranderde - niet in loop gebruiken dus !!

&& RESOURCEFILES van desktop verwijderen -------------------------------------------------------------------------------------------------------
PARAMETERS plCalled,pcCMD,plReport

IF NOT plCalled
	IF NOT VERSION(2)=2
		lcPath = JUSTPATH(SET('RESOURCE',1))
		SET RESOURCE OFF
		ERASE ('&lcPath.\FOXUSER.*')
	ENDIF
	CLEAR ALL
	CLOSE ALL

	&& SYSTEEM-instellingen en instellen op directory waarin het programma ingeladen is ------------------------------------------------------------ 

	PUBLIC pcSAFETY,pcSTRICTDATE,pcROOT,plCalled,pcCMD
	plCalled=.F.

	pcSAFETY=SET('SAFETY')
	SET SAFETY OFF
	pcSTRICTDATE=SET('STRICTDATE')
	SET STRICTDATE TO 0
	SET DATE TO DMY
	SET HOURS TO 24
	SET UDFPARMS TO REFERENCE
	SET COMPATIBLE ON
	SET TALK OFF
	SET CURSOR OFF

	pcROOT=SYS(16)
	pcROOT=LEFT(pcROOT,RAT('\',pcROOT)-1)
	&& SYS(16)=executing programma MET pad, geeft GEEN pad als .APP ! wel als .EXE of .FXP
	CD (pcRoot)
ENDIF

&& Kleuren in constanten zetten ---------------------------------------------------------------------------------------------------------------

PUBLIC pnZwart,pnLichtGrijs,pnGrijs,pnDonkerGrijs,pnWit,;
		 pnLichtRood,pnRood,pnDonkerRood,pnLichtGroen,pnGroen,pnDonkerGroen,;
		 pnLichtBlauw,pnBlauw,pnDonkerBlauw,pnGeel,pnLichtGeel,pnHalfDonkerGeel,pnDonkerGeel,;
		 pnCyaan,pnLichtCyaan,pnHalfDonkerCyaan,pnDonkerCyaan,pnMagenta,pnLichtMagenta

DO INITCOLOR

PUBLIC oSegreg,pnH,pnW
STORE 0 TO pnH,pnW

PUBLIC plStop,plRun,plAbort
STORE .F. TO plStop,plRun,plAbort

PUBLIC pnDist,pnHOffSet,pnVOffSet,pnHPosNON,pnHPosPuC,pnRad
STORE 0 TO pnDist,pnHOffSet,pnVOffSet,pnHPosNON,pnHPosPuC,pnRad

PUBLIC pnSteps,pnStepsTot,pnNONs,pnSUMSS_BUS,pnSUMSS_EUS,pnSatELTP,pnStepFactor
STORE 0 TO pnSteps,pnStepsTot,pnNONs,pnSUMSS_BUS,pnSUMSS_EUS,pnSatELTP,pnStepFactor

PUBLIC plIA
STORE .F. TO plIA

_TOOLTIPTIMEOUT=0

	oSegreg=CREATEOBJECT('SEGREG')
	oSegreg.Show(1)

&& Instellingen herstellen en afsluiten -------------------------------------------------------------------------------------------------------

IF NOT plCalled
	SET STRICTDATE TO &pcSTRICTDATE
	SET SAFETY &pcSAFETY
	SET TALK ON
	RELEASE ALL
	CLEAR ALL
	CLOSE ALL
ENDIF

&& Klasdefinities -----------------------------------------------------------------------------------------------------------------------------

&& COMP SEGREG
DEFINE CLASS SEGREG AS FORM
	WindowState		= 2
	ShowTips			= .T.
	AlwaysOnTop		= .T.
	BackColor		= pnWit
	FontName			= "Courier New"
	FontSize			= 6
	FontBold			= .T.

	lSEGREG		= .F.
	
	PROCEDURE Activate(nX,cAlias)
	IF thisform.lSEGREG
		RETURN
	ENDIF
	thisform.lSEGREG=.T.
	pnH=thisform.Height
	pnW=thisform.Width

	IF NOT FILE("SEGREGMEM.DBF")
		CREATE TABLE SEGREGMEM (NONQTY i(4), LTP n(5,1), LTD n(5,1), CR_TH i(4), LTP_BR_TH i(4), RAND n(5,1), BGN i(4), INICHANCE i(4), STOPLIM i(4))
		APPEND BLANK
		USE IN SEGREGMEM
	ENDIF
	USE SEGREGMEM ALIAS SGM IN SELECT(1)
	SELECT SGM

	PUBLIC ARRAY SS[2,MAX(6,SGM.NONQTY)],SUMSS[2],SUMSSCR1[2],SUMSSCR2[2],TERMS[2]
	SET COMPATIBLE OFF
	STORE 0 TO SS
&&	SET COMPATIBLE ON

	FOR nX=1 TO 6
		cX=LTRIM(STR(nX))
		thisform.AddObject("SG_CBU"+cX,"SG_CBU",6)
	ENDFOR

	FOR nX=1 TO 3
		cX=LTRIM(STR(nX))
		thisform.AddObject("SG_CBD"+cX,"SG_CBD",3)
	ENDFOR

	FOR nX=1 TO 11
		cX=LTRIM(STR(nX))
		thisform.AddObject("SG_SPLB"+cX,"SG_SPLB",11)
		thisform.AddObject("SG_SP"+cX,"SG_SP",11)
	ENDFOR

	IF plCalled
		thisform.Left=pnW/2
		thisform.Width=pnW/2
	ENDIF
	
	IF plCalled
		thisform.DEMO
	ELSE
		thisform.DORUN
	ENDIF
	IF plCalled
		SET COMPATIBLE ON && Must be set ON !! or pnDoc becomes a variable 'not found' on return to the main program !!
		RETURN && !! NOT 'CANCEL' - otherwise windowtype error when restarted, and also remaining interactivity !!
	ENDIF
	RETURN

	PROCEDURE Destroy
	SELECT SGM
	REPLACE NONQTY WITH thisform.SG_SP1.Value, LTP WITH thisform.SG_SP2.Value, LTD WITH thisform.SG_SP3.Value,;
			  CR_TH WITH thisform.SG_SP4.Value, LTP_BR_TH WITH thisform.SG_SP5.Value, RAND WITH thisform.SG_SP6.Value, BGN WITH thisform.SG_SP7.Value,;
			  INICHANCE WITH thisform.SG_SP8.Value, STOPLIM WITH thisform.SG_SP9.Value
	USE IN SGM
	RETURN
	
	PROCEDURE DblClick
	IF thisform.WindowState=2
		thisform.Width=pnW/2
		thisform.Left=pnW/2
		thisform.WindowState=0
	ELSE
		thisform.WindowState=2
	ENDIF
	RETURN

	PROCEDURE DEMO(lNoRun,	nCMD)
	nCMD=VAL(pcCMD)
	plRun=.T.
	SELECT SGM
	REPLACE NONQTY WITH 20, LTP WITH 1.0, LTD WITH 0.1, CR_TH WITH 30, LTP_BR_TH WITH 70, RAND WITH 1, BGN WITH 0, INICHANCE WITH 1, STOPLIM WITH 90
	thisform.LOADSPS
	IF plCalled AND NOT plIA
		thisform.SetAll('Visible',.F.)
		thisform.SG_CBU1.Visible=.T.
		thisform.SG_CBU2.Visible=.T.
		thisform.SG_CBD3.Visible=.T.
	ENDIF
	DO CASE && First DORUN always with .F. to initialize values
	CASE nCMD=1 && Presentation of demo components
		thisform.SETTINGS("ON","ON","I","ON","ON","OFF")
		thisform.DORUN(.F.,100,lNoRun)
	CASE nCMD=2 && Showing thickening lines
		thisform.SETTINGS("ON","ON","I","ON","ON","OFF")
		thisform.DORUN(.F.,345,lNoRun)
	CASE nCMD=3 && Showing Gauss curves
		thisform.SETTINGS("ON","ON","I","ON","ON","OFF")
		thisform.DORUN(.F.,500,lNoRun)
	CASE nCMD=4 && Complete run, intermixed, trace off, showing the segregation process
		thisform.SETTINGS("ON","ON","I","OFF","ON","OFF")
		thisform.DORUN(.F.,6700,lNoRun)
	CASE nCMD=5 && Trace divergence demo with 10 NONs, random function enabled
		thisform.SETTINGS("ON","ON","I","ON","OFF","OFF")
		REPLACE NONQTY WITH 10
		thisform.DORUN(.F.,8000,lNoRun)
	CASE nCMD=6 && Trace divergence demo with 10 NONs, random function disabled
		thisform.SETTINGS("ON","ON","I","ON","OFF","OFF")
		REPLACE NONQTY WITH 10,RAND WITH 0
		thisform.DORUN(.F.,4500,lNoRun)
	CASE nCMD=7 && 'Transfer training' CS1->CS2->CS1 with M-BRAKE OFF
		thisform.SETTINGS("ON","OFF","I","ON","ON","OFF")
		IF lNoRun
			RETURN
		ENDIF
		REPLACE CR_TH WITH 5
		thisform.DORUN(.F.,6700,lNoRun)
		WAIT '' TIMEOUT 2
		thisform.SETTINGS("OFF","ON","I","ON","ON","OFF")
		thisform.DORUN(.T.,6700,lNoRun)
		WAIT '' TIMEOUT 2
		thisform.SETTINGS("ON","OFF","I","ON","ON","OFF")
		thisform.DORUN(.T.,6700,lNoRun)
	CASE nCMD=8 && 'Transfer training' CS1->CS2->CS1 with M-BRAKE ON
		thisform.SETTINGS("ON","OFF","I","ON","ON","ON")
		IF lNoRun
			RETURN
		ENDIF
		REPLACE CR_TH WITH 5
		thisform.DORUN(.F.,6700,lNoRun)
		WAIT '' TIMEOUT 2
		thisform.SETTINGS("OFF","ON","I","ON","ON","ON")
		thisform.DORUN(.T.,5000,lNoRun)
	CASE nCMD=9 && CS1 CS2 INTERMIXED with M-BRAKE ON
		thisform.SETTINGS("ON","ON","I","ON","ON","ON")
		REPLACE CR_TH WITH 5
		thisform.DORUN(.F.,6700,lNoRun)
	CASE nCMD=10 && 'Transfer training' CS1->CS2 with M-BRAKE ON, running longer to watch 'erosion' of CS1
		thisform.SETTINGS("ON","OFF","I","ON","ON","ON")
		IF lNoRun
			RETURN
		ENDIF
		REPLACE CR_TH WITH 5
		thisform.DORUN(.F.,6700,lNoRun)
		WAIT '' TIMEOUT 2
		thisform.SETTINGS("OFF","ON","I","ON","ON","ON")
		REPLACE STOPLIM WITH 100
		thisform.DORUN(.T.,4000,lNoRun)
		WAIT '' TIMEOUT 2
		thisform.SETTINGS("ON","OFF","I","ON","ON","ON")
		REPLACE STOPLIM WITH 90
		thisform.DORUN(.T.,5000,lNoRun)
	CASE nCMD=11 && 'Transfer training' CS1->CS2->CS1 with M-BRAKE ON with M-BRAKE ON AND Background noise
		thisform.SETTINGS("ON","OFF","I","ON","ON","ON")
		REPLACE CR_TH WITH 5
		REPLACE BGN WITH 5
		IF lNoRun
			RETURN
		ENDIF
		thisform.DORUN(.F.,6700,lNoRun)
		WAIT '' TIMEOUT 2
		thisform.SETTINGS("OFF","ON","I","ON","ON","ON")
		thisform.DORUN(.T.,6700,lNoRun)
		WAIT '' TIMEOUT 2
		thisform.SETTINGS("ON","OFF","I","ON","ON","ON")
		thisform.DORUN(.T.,6700,lNoRun)
	CASE nCMD=12 && Interactive mode
		thisform.SetAll('Visible',.T.)
		thisform.SETTINGS("ON","ON","I","ON","ON","ON")
		thisform.DORUN(.F.,0,.T.)
	CASE nCMD=13 && CS1 CS2 COMPOUNDED with M-BRAKE ON AND Background noise
		thisform.SetAll('Visible',.T.)
		thisform.SETTINGS("ON","ON","C","ON","ON","ON")
		REPLACE CR_TH WITH 5
		REPLACE BGN WITH 5, LTD WITH 0
		thisform.DORUN(.F.,2000,lNoRun)
	CASE nCMD=14 && Pretraining with CS2 followed by 'simultaneous' COMPOUND training with CS1 and CS2
		thisform.SetAll('Visible',.T.)
		thisform.SETTINGS("OFF","ON","I","ON","ON","ON")
		IF lNoRun
			RETURN
		ENDIF
		thisform.DORUN(.F.,6700,lNoRun)
		WAIT '' TIMEOUT 2
		thisform.SETTINGS("ON","ON","C","ON","ON","ON")
		REPLACE CR_TH WITH 30, BGN WITH 5, LTD WITH 0
		thisform.DORUN(.T.,4000,lNoRun)
	OTHERWISE
		RETURN
	ENDCASE
	IF thisform.Width>pnW/2
		thisform.DblClick
		thisform.DblClick
	ENDIF
	RETURN

	PROCEDURE SETTINGS(c1,c2,c3,c4,c5,c6,	nX,cX,cCap)
	FOR nX=1 TO 6
		cX=LTRIM(STR(nX))
		cCap=thisform.SG_CBU&cX..Caption
		IF c&cX='O'
			thisform.SG_CBU&cX..Caption=LEFT(cCap,RAT(' ',cCap))+c&cX
			DO CASE
			CASE nX=1
				thisform.SG_CBU1.ForeColor=IIF(c&cX="ON",pnRood,pnWit)
			CASE nX=2
				thisform.SG_CBU2.ForeColor=IIF(c&cX="ON",pnBlauw,pnWit)
			ENDCASE
		ELSE
			thisform.SG_CBU&cX..Caption=IIF(c3='I',"INTERMIXED","COMPOUNDED")
			thisform.SG_CBU&cX..Tag=thisform.SG_CBU&cX..Caption
		ENDIF
	ENDFOR
	RETURN
	
	PROCEDURE LOADSPS
	SELECT SGM
	IF LTP>0
		thisform.SG_SP1.Value=NONQTY
		thisform.SG_SP2.Value=LTP
		thisform.SG_SP3.Value=LTD
		thisform.SG_SP4.Value=CR_TH
		thisform.SG_SP5.Value=LTP_BR_TH
		thisform.SG_SP6.Value=RAND
		thisform.SG_SP7.Value=BGN
		thisform.SG_SP8.Value=INICHANCE
		thisform.SG_SP9.Value=STOPLIM
	ENDIF
	RETURN
	
	PROCEDURE DORUN(lCont,nSteps,lNoRun,	nX,nY,lCS,lCS1,lCS2,lCS1Mem,lCS2Mem,lCPD,nCS,nSS12,nF,nSH,nK,nVO,nSUMSS_TH)
	IF lNoRun
		RETURN
	ENDIF
	&& INITIATIE
	pnHOffSet=80 && Horizontal offset
	pnVOffSet=75 && Vertical offset
	pnDist=380/SGM.NONQTY && Distance between NONs
	pnHPosNON=200 && Position of NON columnn
	pnHPosPuC=315 && Position of PuC columnn
	pnRad=10 && radius
	IF thisform.SG_CBD1.Caption="RUN"
		thisform.Width=pnW/2
		thisform.Left=pnW/2
	ENDIF
	thisform.LOADSPS

	DIMENSION SS[2,MAX(6,SGM.NONQTY)],SUMSS[2],SUMSSCR1[2],SUMSSCR2[2],TERMS[2]
	RAND(-1)
	IF NOT lCont && If it is NOT a 'continuing' of an earlier procedure then we initialize the values, so cont=.F. the first time
		STORE 0 TO pnSteps,pnStepsTot
		FOR nX=1 TO 2
			SUMSS(nX)=0
			SUMSSCR1(nX)=0
			SUMSSCR2(nX)=0
			TERMS(nX)=REPLICATE(CHR(0),SGM.NONQTY)
			FOR nY=1 TO SGM.NONQTY
				SS(nX,nY)=0
			ENDFOR
		ENDFOR
	ENDIF

	IF NOT plRun
		RETURN
	ENDIF

&&	RENDERING SECTION vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv

	nK=0
	nSH=70
	thisform.ForeColor=pnZwart
	nVO=pnVOffSet+pnDist*(SGM.NONQTY-1)+10
	thisform.Print("MFs",(pnHOffSet+pnHPosNON)/2,nVO+5)
	thisform.Print("NONs",pnHPosNON-pnRad,nVO+5)
	thisform.Print("CFs",(pnHPosNON+pnHPosPuC+IIF(SGM.NONQTY>15,nSH,0))/2-pnRad/2,nVO+5)
	thisform.Print("PuCs",pnHPosPuC+IIF(SGM.NONQTY>15,nSH,0)-pnRad,nVO+5)

	nVO=nVO+60
	thisform.ForeColor=pnRood
	thisform.Line(0,pnVOffSet,        pnHOffSet,pnVOffSet) && Hor MF lijn
	thisform.Print("800 ms",60,nVO/2-20)

	thisform.ForeColor=pnBlauw
	thisform.Line(0,pnVOffSet+pnDist*(SGM.NONQTY-1),pnHOffSet,pnVOffSet+pnDist*(SGM.NONQTY-1)) && Hor MF lijn
	thisform.Print("400 ms",14,nVO/2+115)

&&	RENDERING SECTION ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

	lCS1=( thisform.SG_CBU1.Caption="CS1 ON" )
	lCS1Mem=lCS1
	lCS2=( thisform.SG_CBU2.Caption="CS2 ON" )
	lCS2Mem=lCS2
	lCPD=( thisform.SG_CBU3.Caption="COMPOUNDED" )
	IF lCPD
		lCS1=.F.
	ENDIF
	thisform.SG_CBU1.ForeColor=IIF(lCS1,pnRood,pnWit)
	thisform.SG_CBU2.ForeColor=IIF(lCS2,pnBlauw,pnWit)

	pnSatELTP=10 && the LTP saturation limit of the NON (for all CS input together in 'population view')
	pnSatBLTP=pnSatELTP*SGM.LTP_BR_TH/100 && The set threshold above which the LTP brake starts to have effect

	pnMaxSumSS=10*SGM.NONQTY/2 && Het max dat de som van SS van MF-NON lijnen kan bereiken voor elk van de twee CSn (10 is sat level LTP)
	pnCR_TH=pnMaxSumSS*SGM.CR_TH/100 && De afgesproken drempel (% van pnMaxSumSS) vanaf wanneer het US effect begint af te zwakken 
	nSUMSS_TH=pnSatELTP*SGM.NONQTY*SGM.CR_TH/100
	DO WHILE pnSteps<IIF(VARTYPE(nSteps)='N',nSteps,100000)
		DO CASE
		CASE lCS1=.F. AND lCS2=.F. && No CS selected
			EXIT
		CASE lCPD && Switches CS1=.F./CS2=.T. with CS1=.T./CS2=.F. (therefore CS1 must be =.F. at the start)
			lCS=lCS1
			lCS1=lCS2
			lCS2=lCS
			thisform.SG_CBU1.ForeColor=pnRood
		CASE lCS1Mem AND lCS2Mem && when 'Intermixed' CS1 and CS2 are chosen at random in equal frequency
			lCS1=IIF(RAND()<.5000,.T.,.F.)
		CASE lCS1Mem && Background noise ! lCS1=.T. but in SGM.BGN/100 of cases it is .F. and then lCS2 will be .T.
			lCS1=IIF(RAND()<1-SGM.BGN/100,.T.,.F.)
		CASE lCS2Mem && Background noise ! lCS2=.T. but in SGM.BGN/100 of cases it is .F. and then lCS1 will be .T.
			lCS1=IIF(RAND()<SGM.BGN/100,.T.,.F.)
		ENDCASE

		lCS2=NOT lCS1
		nCS=IIF(lCS1,1,2)

		TERMS(1)=REPLICATE(CHR(0),SGM.NONQTY)
		TERMS(2)=REPLICATE(CHR(0),SGM.NONQTY)
		thisform.CSALL(nCS,lCPD)

&&		RENDERING SECTION vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv

		nF=(20/100)*20/SGM.NONQTY && to keep the maximum curve top equally high when different numbers of NONs are displayed
		nVO=pnVOffSet+pnDist*(SGM.NONQTY-1)/2
		IF INT(pnSteps/10)=pnSteps/10
			nDW=1
			thisform.ForeColor=thisform.BackColor && Erasing the curves
			thisform.GAUSS(nVO-20	,46	,SUMSSCR1(1)*nF,nDW) && CR by CS1 via timers of CS1 ('tone' with US at 800 ms)
			thisform.GAUSS(nVO-20	,0 	,SUMSSCR2(1)*nF,nDW) && CR by CS2 via timers of CS1 ('tone' with US at 800 ms)
			thisform.GAUSS(nVO+115	,0		,SUMSSCR2(2)*nF,nDW) && CR by CS2 via timers of CS2 ('light' with US at 400 ms)
			thisform.GAUSS(nVO+115 	,46 	,SUMSSCR1(2)*nF,nDW) && CR by CS1 via timers of CS2 ('light' with US at 400 ms)
			&& -20 = curves bij testing van CS1, +115 = curves bij testing van CS2
			&& '0' = 400 ms, '46' = 800 ms

			thisform.SUM_SSCR(nCS,lCPD) && Get the new SUMSS values 

			&& Drawing the curves of CS1 on the basis of the sum of SSs
			thisform.ForeColor=pnRood

			IF lCPD
			&& If two CSs "cooperate" in 'compound' we must also check if the individual CS has enough power to activate CFs
			&& since once it does it activates timers of CS1 as well as CS2
			&& and if e.g. CS1 is still very weak it should not activate timers made by CS2
				IF SUMSS(1)+SUMSS(2)>nSUMSS_TH
					thisform.GAUSS(nVO-20	,46	,SUMSSCR1(1)*nF,nDW) && CR by CS1 via timers of CS1 ('tone' with US at 800 ms)
					IF SUMSS(2)>nSUMSS_TH
						thisform.GAUSS(nVO+115 	,46		,SUMSSCR1(2)*nF,nDW) && CR by CS1 via timers of CS2 ('tone' with US at 800 ms)
					ENDIF
				ENDIF

			&& Drawing the curves of CS2
				thisform.ForeColor=pnBlauw 

				IF SUMSS(2)+SUMSS(1)>nSUMSS_TH
					thisform.GAUSS(nVO+115	,0		,SUMSSCR2(2)*nF,nDW) && CR by CS2 via timers of CS2 ('light' with US at 400 ms)
					IF SUMSS(1)>nSUMSS_TH
						thisform.GAUSS(nVO-20	,0 	,SUMSSCR2(1)*nF,nDW) && CR by CS2 via timers of CS1 ('light' with US at 400 ms
					ENDIF
				ENDIF
			ELSE
&&				IF SUMSS(1)>nSUMSS_TH
					thisform.GAUSS(nVO-20	,46	,SUMSSCR1(1)*nF,nDW) && CR by CS1 via timers of CS1 ('tone' with US at 800 ms)
&&					IF SUMSS(2)>nSUMSS_TH
						thisform.GAUSS(nVO+115 	,46		,SUMSSCR1(2)*nF,nDW) && CR by CS1 via timers of CS2 ('tone' with US at 800 ms)
&&					ENDIF
&&				ENDIF

				&& Drawing the curves of CS2
				thisform.ForeColor=pnBlauw 

&&				IF SUMSS(2)>nSUMSS_TH
					thisform.GAUSS(nVO+115	,0		,SUMSSCR2(2)*nF,nDW) && CR by CS2 via timers of CS2 ('light' with US at 400 ms)
&&					IF SUMSS(1)>nSUMSS_TH
						thisform.GAUSS(nVO-20	,0 	,SUMSSCR2(1)*nF,nDW) && CR by CS2 via timers of CS1 ('light' with US at 400 ms
&&					ENDIF
&&				ENDIF
			ENDIF
		ENDIF

		pnStepFactor=30 && determines progression speed of trace and 'background' on the screen
		IF pnSteps/pnStepFactor=INT(pnSteps/pnStepFactor)
			IF pnHPosPuC+IIF(SGM.NONQTY>15,70,0)+10+pnSteps/pnStepFactor>thisform.Width-5 && the screen starts to shift left
				thisform.Width=thisform.Width+1
				thisform.Left=thisform.Left-1
			ENDIF
		ENDIF
		IF pnHPosPuC+IIF(SGM.NONQTY>15,70,0)+10+pnSteps/pnStepFactor>pnW && when full screen is attained, restart display in half screen 
			thisform.Cls
			pnSteps=0
		ENDIF
		pnSteps=pnSteps+1
		pnStepsTot=pnStepsTot+1

&&		IF SUMSS(1)>0
			thisform.ForeColor=pnRood
			thisform.Print("Sum CS1="+STR(SUMSS(1),7,2),5,pnVOffSet-15) && SUM of all CS1 SSs
			thisform.Print("CS1 : "+LTRIM(STR(LEN(TERMS(1))-OCCURS(CHR(0),TERMS(1))-OCCURS(CHR(1),TERMS(1))))+" terminals  ",5,pnVOffSet-25)
			&& Count of connected CS1 terminals
&&		ENDIF
&&		IF SUMSS(2)>0
			thisform.ForeColor=pnBlauw
			thisform.Print("Sum CS2="+STR(SUMSS(2),7,2),5,pnVOffSet+pnDist*(SGM.NONQTY-1)+6) && SUM of all CS2 SSs
			thisform.Print("CS2 : "+LTRIM(STR(LEN(TERMS(2))-OCCURS(CHR(0),TERMS(2))-OCCURS(CHR(1),TERMS(2))))+" terminals  ",5,pnVOffSet+pnDist*(SGM.NONQTY-1)+16)
			&& Count of connected CS2 terminals
&&		ENDIF
		thisform.ForeColor=pnZwart
		thisform.Print(LTRIM(STR(pnStepsTot))+" steps ",5,pnVOffSet+pnDist*(SGM.NONQTY-1)/2-6) && StepCount

&&		RENDERING SECTION ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

		DOEVENTS

		&& Ending the procedure

		IF lCS1Mem=.F. OR    OCCURS(CHR(100),TERMS(1))=>SGM.NONQTY/2 AND SUMSS(1)>pnSUMSS_EUS*SGM.STOPLIM/100
			IF lCS2Mem=.F. OR OCCURS(CHR(100),TERMS(2))=>SGM.NONQTY/2 AND SUMSS(2)>pnSUMSS_EUS*SGM.STOPLIM/100
				IF nK=300 && keep running for 300 steps after ending requirements are fulfilled
&&					thisform.SG_CBD1.Caption="CONTINUE"
					EXIT
				ENDIF
				nK=nK+1
			ENDIF
		ENDIF

		&& Stopping / Interrupting the procedure

		IF thisform.SG_SP11.Value>0 AND INT(pnSteps/thisform.SG_SP11.Value)=pnSteps/thisform.SG_SP11.Value && Interrupt after each x steps when desired
			thisform.SG_CBD2.MouseDown && Stop button
		ENDIF

		IF plStop
			plStop=.F.
			thisform.SG_CBD1.Caption="CONTINUE"
			EXIT
		ENDIF
		
		&& Aborting the procedure

		IF plAbort
			thisform.SG_CBD1.Caption="RUN"
			EXIT
		ENDIF

	ENDDO
	FOR nX=1 TO SGM.NONQTY
		nVO=pnVOffSet+pnDist*(nX-1)
		thisform.ForeColor=pnRood
		thisform.LINEDRAW(1,SS(1,nX)+1,.T.,nVO) && Erasing
		IF SS(1,nX)>.1
			thisform.LINEDRAW(1,SS(1,nX),.F.,nVO) && Redrawing
		ENDIF
		thisform.ForeColor=pnBlauw
		thisform.LINEDRAW(2,SS(2,nX)+1,.T.,nVO) && Erasing
		IF SS(2,nX)>.1
			thisform.LINEDRAW(2,SS(2,nX),.F.,nVO) && Redrawing
		ENDIF
		&& Redrawing of NONs to erase overlying line endings
		thisform.DrawWidth=1
		thisform.FillColor=pnCyaan
		thisform.Circle(pnRad,pnHPosNON,nVO)
	ENDFOR
	thisform.SetAll("Enabled",.T.,"SG_SP")
	?? CHR(7)
	RETURN
	
	PROCEDURE CSALL(nCS,lCPD)
	thisform.SUM_SS
	thisform.LTPD(nCS,lCPD)
	thisform.DEL_TERM
	thisform.ADD_TERM(nCS,lCPD)
	RETURN
	
	&& US present from beginning, LTPing active synapses, LTDing inactive synapses, geometrically.
	&& PuC timed CRs can only start to develop when individual NONs become able to HP-R IO cells (hence from an LTP threshold on) 
	&& US only starts to dwindle when overt CRs appear, i.e. above a threshold of summed SS of the CS
	&&    to disappear gradually above a limit of summed SS
	
	&& Terminals are supposed to increase with US strength (and stop to do so when US dwindles)
	&&    hence at a constant rate when US stays constant, but it should be much slower than LTP increase.
	&& Terminals 'disengage' when LTP goes under a limit
	&& Terminals also 'disengage' when US strength goes under a limit

	PROCEDURE LTPD(nCSP,lCPD,		nSH,nCSD,nCSColor,nX,nVO,nMemSSP,nMemSSD,nSS12,nMixColor,nV,nUS_Brake,nSS)
	nCSD=IIF(nCSP=1,2,1) && nCSP refers to the active synapse, nCSD to the inactive one

	&& Rendering settings
	nSH=70
	thisform.FillStyle=0 && Solid.
	nCSColor=IIF(nCSP=1,pnRood,pnBlauw)
	thisform.ForeColor=nCSColor

	&& Calculations per NON
	FOR nX=1 TO SGM.NONQTY
		nMemSSP=SS(nCSP,nX)
		nMemSSD=SS(nCSD,nX)
		&& Calculation of LTP on the active synapse
		nSS12=SS(1,nX)+SS(2,nX) && the sum of the two synapses on the NON
		IF lCPD && In case of 'compound' CS1 and CS2 training
			pnSUMSS_EUS=pnSatELTP*SGM.NONQTY/2 && at this value of SUMSS the US is neutralized by negative feedback from the CR
			pnSUMSS_BUS=SGM.CR_TH && at this value of SUMSS (of active synapses) the US starts to be subdued by an upcoming CR
			&& When SGM.CR_TH is set low a long period of double peaks appears, if set high they may not appear at all 
			nUS_Brake=(SUMSS(1)+SUMSS(2)-pnSUMSS_BUS)/(pnSUMSS_EUS-pnSUMSS_BUS)
			nUS_Brake=pnSUMSS_EUS*IIF(SUMSS(1)+SUMSS(2)<pnSUMSS_BUS,1,1-nUS_Brake)
			&& Range 0 to 1, is inverse parameter of US strength
			&& Depends on the strength of ALL ACTIVE synapses
			&& Effect starts to show when SUMSS=>pnSUMSS_BUS

			nLTP_Brake=(nSS12-pnSatBLTP)/(pnSatELTP-pnSatBLTP)
			nLTP_Brake=pnSatELTP*IIF(nSS12<pnSatBLTP,1,1-nLTP_Brake)
			SS(1,nX)=SS(1,nX)*			(1+	SS(1,nX)	*SGM.LTP	*nLTP_Brake	*	nUS_Brake	*(RAND()*SGM.RAND/10+.5)/10000)
			SS(2,nX)=SS(2,nX)*			(1+	SS(2,nX)	*SGM.LTP	*nLTP_Brake	*	nUS_Brake	*(RAND()*SGM.RAND/10+.5)/10000)

		ELSE && In case of 'intermixed' CS1 and CS2 training
			pnSUMSS_EUS=pnSatELTP*SGM.NONQTY/2 && at this value of SUMSS the US is neutralized by negative feedback from the CR
			pnSUMSS_BUS=SGM.CR_TH && at this value of SUMSS (of active synapses) the US starts to be subdued by an upcoming CR
			&& When SGM.CR_TH is set low a long period of double peaks appears, if set high they may not appear at all 
			nUS_Brake=(SUMSS(nCSP)-pnSUMSS_BUS)/(pnSUMSS_EUS-pnSUMSS_BUS)
			nUS_Brake=pnSUMSS_EUS*IIF(SUMSS(nCSP)<pnSUMSS_BUS,1,1-nUS_Brake)
			&& Range 0 to 1, is inverse parameter of US strength
			&& Depends on the strength of ALL ACTIVE synapses
			&& Effect starts to show when SUMSS=>pnSUMSS_BUS

			nSS=IIF(thisform.SG_CBU6.Caption="METAB.BRAKE ON",nSS12,SS(nCSP,nX))
			nLTP_Brake=(nSS-pnSatBLTP)/(pnSatELTP-pnSatBLTP)
			nLTP_Brake=pnSatELTP*IIF(nSS<pnSatBLTP,1,1-nLTP_Brake)
			SS(nCSP,nX)=SS(nCSP,nX)*	(1+	SS(nCSP,nX)	*SGM.LTP	*nLTP_Brake	*	nUS_Brake	*(RAND()*SGM.RAND/10+.5)/10000)
		ENDIF

		SS(nCSP,nX)=MAX(0,SS(nCSP,nX)) && protect against negative undershoots
		&& LTP is a function of actual ACTIVE SS, LTP gain, distance to LTP saturation, US strength (dwindles above CR-TH), and a random factor

		&& Calculation of LTD on the inactive synapse (when 'compounded' there is NO LTD !!)
		IF NOT lCPD
			SS(nCSD,nX)=SS(nCSD,nX)	*(1-	MIN(1,SS(nCSP,nX)	*SGM.LTD	*(RAND()*SGM.RAND/10+.5)/100))
			&& LTD is a function of actual INACTIVE CS, LTD gain,
			&& but also of actual ACTIVE SS (and hence also of all factors determining LTP), and a random factor
			SS(nCSD,nX)=MAX(0,SS(nCSD,nX)) && protect against negative undershoots
		ENDIF

		nSS12=SS(1,nX)+SS(2,nX)

		&& To keep track inhowfar each 'terminal' is saturated (i.e. when = 100, and all active terminals saturated, the process can stop
		IF nSS12>0
			TERMS(nCSP)=STUFF(TERMS(nCSP),nX,1,CHR((SS(nCSP,nX)*100)/nSS12))
			TERMS(nCSD)=STUFF(TERMS(nCSD),nX,1,CHR((SS(nCSD,nX)*100)/nSS12))
		ENDIF

&&		RENDERING SECTION vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv

		&& erasing of active MF-NON lines en redrawing them when the width changed
		nVO=pnVOffSet+pnDist*(nX-1)
		IF INT(nMemSSP)#INT(SS(nCSP,nX)) OR nMemSSP<1 OR pnSteps<100 OR INT(pnSteps/100)=pnSteps/100
			IF nMemSSP>0.05 && als 0 blijven gewiste strepen, als 1 blijven kleurlijnen van 1 staan, .5 lost het op
				thisform.LINEDRAW(nCSP,nMemSSP+2,.T.,nVO) && Erasing
			ENDIF
			thisform.LINEDRAW(nCSP,SS(nCSP,nX),.F.,nVO) && Redrawing
		ENDIF
		&& erasing of inactive MF-NON lines en redrawing them when the width changed
		IF INT(nMemSSD)#INT(SS(nCSD,nX)) OR nMemSSD<1 OR pnSteps<100 OR INT(pnSteps/100)=pnSteps/100
			IF nMemSSD>0.05
				thisform.LINEDRAW(nCSD,nMemSSD+2,.T.,nVO) && Erasion
			ENDIF
			thisform.LINEDRAW(nCSD,SS(nCSD,nX),.F.,nVO) && Redrawing
		ENDIF

		&& Relative and absolute values of CS1-SS and CS2-SS
		IF SGM.NONQTY<=26
			IF SGM.NONQTY>15
				thisform.ForeColor=pnRood
				thisform.Print(STR(SS(1,nX)*100/nSS12,4)+" CS1="+STR(SS(1,nX),7,3)+' ',;
									pnHPosNON+7,nVO-8-4) && Figures above the horizontal NON-PuC line
				thisform.ForeColor=pnBlauw
				thisform.Print(STR(SS(2,nX)*100/nSS12,4)+" CS2="+STR(SS(2,nX),7,3)+' ',;
									pnHPosNON+17+nSH,nVO-8-4) && Figures above the horizontal NON-PuC line
			ELSE
				thisform.ForeColor=pnRood
				thisform.Print(STR(SS(1,nX)*100/nSS12,4)+" CS1="+STR(SS(1,nX),7,3)+' ',;
									pnHPosNON+12,nVO-8-5) && Figures above the horizontal NON-PuC line
				thisform.ForeColor=pnBlauw
				thisform.Print(STR(SS(2,nX)*100/nSS12,4)+" CS2="+STR(SS(2,nX),7,3)+' ',;
									pnHPosNON+12,nVO+8-4) && Figures under the horizontal NON-PuC line
			ENDIF
		ENDIF
		&& Erasing the horizontal line between NON and PuC
		thisform.ForeColor=thisform.BackColor
		thisform.DrawWidth=5
		thisform.Line(pnHPosNON,nVO,pnHPosPuC+IIF(SGM.NONQTY>15,nSH,0),nVO)

		&& Redrawing the horizontal line between NON and PuC
		nMixColor=RGB(INT(255*SS(1,nX)/nSS12),0,INT(255*SS(2,nX)/nSS12)) && Mixed colour of the horizontale line
		IF nMixColor>0
			thisform.ForeColor=nMixColor
			thisform.DrawWidth=IIF(nSS12>ABS(SGM.CR_TH)/10,5,1) && Lijndikte horizontale lijn
			&& The maximum of nSS12 is 20 (2 synapses of max 10 when saturated)
			&& SGM.CR_TH/10 goes from 0 to 10
			&& CR-TH is used here as the threshold above which CF firing starts
			&& while elsewhere it is used as the threshold above which the CR starts to appear
			&& The thickening of the line is 'cosmetic' and the CF threshold is of no further consequence in the calculation
			&& because a higher CR threshold follows
			&& It would complicate needlesly the calculation to implement a 'two-stage threshold'
			thisform.Line(pnHPosNON,nVO,pnHPosPuC+IIF(SGM.NONQTY>15,nSH,0),nVO)
			thisform.DrawWidth=1
			thisform.FillColor=nMixColor
			thisform.Circle(pnRad,pnHPosPuC+IIF(SGM.NONQTY>15,nSH,0),nVO) && draws a full circle PuC of the same colour as the NON-PuC line
		ENDIF

		&& Background progress
		IF thisform.SG_CBU5.Caption="BACKGROUND ON"
			thisform.ForeColor=nMixColor
			thisform.DrawWidth=1
			IF nSS12>ABS(SGM.CR_TH)/10 AND nMixColor>0
				thisform.Line(pnHPosPuC+IIF(SGM.NONQTY>15,nSH,0)+10+pnSteps/pnStepFactor,nVO-pnDist/2,;
								  pnHPosPuC+IIF(SGM.NONQTY>15,nSH,0)+10+pnSteps/pnStepFactor,nVO+pnDist/2+1)
				&& bij meer dan 15 NONs verbreden we de afstand NON-PuC en dan moet alles een afstand nSH opschuiven
			ENDIF
		ENDIF
		&& Trace progress
		IF thisform.SG_CBU4.Caption="TRACE ON" AND IIF(nCSP=1,SS(1,nX),SS(2,nX))>0
			thisform.ForeColor=nCSColor
			thisform.DrawWidth=1
			thisform.PSET(pnHPosPuC+IIF(SGM.NONQTY>15,nSH,0)+9+pnSteps/pnStepFactor,nVO+1-(20/SGM.NONQTY)*IIF(nCSP=1,SS(1,nX),SS(2,nX)))
			&& Horizontal shift when NONs>15
		ENDIF
		
		&& Redrawing of NONs to erase overlying line endings
		thisform.FillColor=pnCyaan
		thisform.Circle(pnRad,pnHPosNON,nVO)

&&		RENDERING SECTION ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

	ENDFOR
	RETURN

	PROCEDURE SUM_SS(nX)
	SUMSS(1)=0
	SUMSS(2)=0
	FOR nX=1 TO SGM.NONQTY
		SUMSS(1)=SUMSS(1)+SS(1,nX)
		SUMSS(2)=SUMSS(2)+SS(2,nX)
	ENDFOR
	RETURN

	PROCEDURE SUM_SSCR(nCS,lCPD,	nX,nSS12,nSS_TH) && Has to represent the CRs when testing is done for CS1 or CS2 ALONE !!!
	STORE 0 TO SUMSSCR1(1),SUMSSCR1(2),SUMSSCR2(1),SUMSSCR2(2)
	&& Calculation of CR strength
	&& It is assumed that the (evt combined) SS of the NON determines the strength of CF firing
	&& and that this in turn determines the strength of HP in the PuC (by the number of activated timer)
	&& (the two-stage threshold), and hence 'activating CF' means 'activating the CR'
	nSS_TH=pnSatELTP*SGM.CR_TH/100
	IF lCPD
		&& The upper peaks show the CR components of CS1 and CS2 that will fuse when tested for T (displaying an acceleration effect)
		&& The lower peaks show the CR components of CS1 and CS2 that will fuse when tested for L (displaying a deceleration effect)
		
		&& However, the demo setup only shows the nanoloop population that has to be 'segregated'.
		&& In vivo, there will be other nanoloop populations which from the start on are CS1 only or CS2 only
		&& and these components have to be added to complete the final picture
		 
		FOR nX=1 TO SGM.NONQTY && For all NONs
			nSS12=SS(1,nX)+SS(2,nX)
			IF nSS12>nSS_TH && CS1 + CS2 strong enough to trigger the CF-PuC-CR chain
				SUMSSCR1(1)=SUMSSCR1(1)+SS(1,nX) && SS gives a measure of how much timers were produced by CS1
				SUMSSCR2(1)=SUMSSCR2(1)+SS(2,nX) && SS gives a measure of how much timers were produced by CS2
				SUMSSCR1(2)=SUMSSCR1(2)+SS(1,nX) && SS gives a measure of how much timers were produced by CS1
				SUMSSCR2(2)=SUMSSCR2(2)+SS(2,nX) && SS gives a measure of how much timers were produced by CS2
			ENDIF
		ENDFOR
	ELSE
		FOR nX=1 TO SGM.NONQTY && For all NONs
			IF SS(1,nX)>nSS_TH && CS1 strong enough to trigger the CF-PuC-CR chain
				&& Only the SSs of nanoloops that can trigger a CF are included for the summing
				SUMSSCR1(1)=SUMSSCR1(1)+SS(1,nX) && SS gives a measure of how much timers were produced by CS1 (CS1 U 800)
				SUMSSCR2(1)=SUMSSCR2(1)+SS(2,nX) && SS gives a measure of how much timers were produced by CS2 (CS2 U 400)
			ENDIF
			IF SS(2,nX)>nSS_TH && CS2 strong enough to trigger the CF-PuC-CR chain
				SUMSSCR2(2)=SUMSSCR2(2)+SS(2,nX) && SS gives a measure of how much timers were produced by CS2 (CS2 D 400)
				SUMSSCR1(2)=SUMSSCR1(2)+SS(1,nX) && SS gives a measure of how much timers were produced by CS1 (CS1 D 800) 
			ENDIF
		ENDFOR
	ENDIF
	&& Het resultaat geeft sterkten voor vier 'CR-curves'
	&& Twee voor activatie door CS1 en twee voor activatie door CS2
	&& Als CS1 en CS2 verschilden in ISI tov US dan worden de componenten uitgevoerd na de specifieke ISI (400 of 800 ms)
	RETURN

	PROCEDURE DEL_TERM(nX,nVO)
	FOR nX=1 TO SGM.NONQTY
		nVO=pnVOffSet+pnDist*(nX-1)
		IF SS(1,nX)<.1 AND SS(1,nX)>0
		&& Als terminal sterkte onder .1 wordt hij 'gelost' : als op 0 niet meer gevoelig voor LTP
			SS(1,nX)=0
			thisform.LINEDRAW(1,1,.T.,nVO) && MF-NON lijn wissen
		ENDIF
		IF SS(2,nX)<.1 AND SS(2,nX)>0
		&& Als terminal sterkte onder .1 wordt hij 'gelost' : als op 0 niet meer gevoelig voor LTP
			SS(2,nX)=0
			thisform.LINEDRAW(2,1,.T.,nVO) && MF-NON lijn wissen
		ENDIF
	ENDFOR
	RETURN

	PROCEDURE ADD_TERM(nCS,lCPD,	nCSD,nX,nTR,nUS_Brake,nSS12)
	nCSD=IIF(nCS=1,2,1)
	STORE 0 TO nUS_Brake,nSS12
	FOR nX=1 TO SGM.NONQTY
		IF lCPD
			IF thisform.SG_CBU6.Caption="METAB.BRAKE ON"
				nSS12=(SS(1,nX)+SS(2,nX))/10
				&& SS range 0 tot 10, is parameter for LTP strength
				&& the more SS approaches LTPMAX (lim=10) the smaller the chance to make a connection
				&& both active and inactive SS values are combined now
			ENDIF

			IF SS(1,nX)=0 AND SUMSS(1)<pnSUMSS_EUS && Als er geen connectie is , en als er nog geen sat van alle lijnen is
				nUS_Brake=0 &&IIF(SUMSS(nCS)<pnSUMSS_BUS,0,(SUMSS(nCS)-pnSUMSS_BUS)/(pnSUMSS_EUS-pnSUMSS_BUS))
				&& Range 0 to 1, is inverse parameter of US strength
				&& the more (from pnSUMSS_BUS on) SUMSS approaches pnSUMSS_EUS the smaller the chance to make a connection
				nTR=SGM.INICHANCE+5000*nUS_Brake+5000*nSS12
				IF BETWEEN(RAND()*nTR*SGM.RAND/10,0,1)
					SS(1,nX)=.1 && When set = 0.1 'sensitivity' for LTP returns
				ENDIF
			ENDIF
			IF SS(2,nX)=0 AND SUMSS(2)<pnSUMSS_EUS && Als er geen connectie is , en als er nog geen sat van alle lijnen is
				nUS_Brake=0 &&IIF(SUMSS(nCS)<pnSUMSS_BUS,0,(SUMSS(nCS)-pnSUMSS_BUS)/(pnSUMSS_EUS-pnSUMSS_BUS))
				&& Range 0 to 1, is inverse parameter of US strength
				&& the more (from pnSUMSS_BUS on) SUMSS approaches pnSUMSS_EUS the smaller the chance to make a connection
				nTR=SGM.INICHANCE+5000*nUS_Brake+5000*nSS12
				IF BETWEEN(RAND()*nTR*SGM.RAND/10,0,1)
					SS(2,nX)=.1 && When set = 0.1 'sensitivity' for LTP returns
				ENDIF
			ENDIF
		ELSE
			IF SS(nCS,nX)=0 AND SUMSS(nCS)<pnSUMSS_EUS && Als er geen connectie is , en als er nog geen sat van alle lijnen is
				nUS_Brake=0 &&IIF(SUMSS(nCS)<pnSUMSS_BUS,0,(SUMSS(nCS)-pnSUMSS_BUS)/(pnSUMSS_EUS-pnSUMSS_BUS))
				&& Range 0 to 1, is inverse parameter of US strength
				&& the more (from pnSUMSS_BUS on) SUMSS approaches pnSUMSS_EUS the smaller the chance to make a connection
				IF thisform.SG_CBU6.Caption="METAB.BRAKE ON"
					nSS12=(SS(nCS,nX)+SS(nCSD,nX))/10
					&& SS range 0 tot 10, is parameter for LTP strength
					&& the more SS approaches LTPMAX (lim=10) the smaller the chance to make a connection
					&& both active and inactive SS values are combined now
				ENDIF
				nTR=SGM.INICHANCE+5000*nUS_Brake+5000*nSS12
				IF BETWEEN(RAND()*nTR*SGM.RAND/10,0,1)
					SS(nCS,nX)=.1 && When set = 0.1 'sensitivity' for LTP returns
				ENDIF
			ENDIF
		ENDIF
	ENDFOR
	RETURN
	
	PROCEDURE LINEDRAW(nCS,nW,lWis,nV)
	IF lWis
		thisform.ForeColor=thisform.BackColor
	ELSE
		thisform.ForeColor=IIF(nCS=1,pnRood,pnBlauw)
	ENDIF
	thisform.DrawWidth=nW
	IF nW>0.05
		IF nW<1
			thisform.DrawStyle=2
			thisform.DrawWidth=1
		ENDIF
		thisform.Line(pnHOffSet,pnVOffSet+pnDist*IIF(nCS=1,0,SGM.NONQTY-1),pnHPosNON-pnRad,nV) && Lijn van MF naar NON
		thisform.DrawStyle=0
	ENDIF
	RETURN
	
	PROCEDURE GAUSS(nVOffSet,nHOffSet,nHeight,nDW,	nHeight2,nWidth,nTopHOffSet,nX,nS)
	thisform.DrawWidth=nDW
	nHeight2=20
	nWidth=16
	nTopHOffSet=26
	FOR nX=1 TO 50
		nS=INT(4+nHeight*(INT(nHeight2/7)+1)*EXP(1)^(((-4*LOG(2))*(nX-nTopHOffSet)^2)/nWidth^2))
		thisform.PSet(nX+nHOffSet,nVOffSet-nS)
	ENDFOR
	RETURN

ENDDEFINE

DEFINE CLASS SG_CBU AS LABEL
	FontBold			= .T.
	Top				= 0
	Height			= 20
	Visible			= .T.
	FontSize			= 8
	Alignment		= 2
	BorderStyle		= 1

	PROCEDURE Init(nMax,	nX,cTTT)
	nX=VAL(RIGHT(this.Name,1))
	this.Width=(pnW/2)/nMax
	this.Left=(nX-1)*this.Width
	this.Caption=STREXTRACT(",CS1 OFF,CS2 OFF,---,TRACE ON,BACKGROUND ON,METAB.BRAKE ON,",',',',',nX)
	this.Tag=this.Caption
	this.ForeColor=IIF(nX<3,pnWit,pnZwart)
	this.BackColor= pnCyaan
	DO CASE
	CASE nX=3
		this.Enabled=.F.
		this.Tag="INTERMIXED"
		this.ToolTipText="When 'INTERMIXED' CS1 and CS2 are activated alternately (but still randomly),"+CHR(13)+;
							  "when 'COMPOUNDED' CS2 always follows CS1 and only then is the US supposed to happen :"+CHR(13)+;
							  "Programmatically it is implemented by disabling LTD (since both CSs are active when the US occurs)"+CHR(13)+;
							  "and by using the combined sums of SSs in the calculations."
	CASE nX=6
		this.ToolTipText="Activating the 'metabolic brake' is a 'shift of view' :"+CHR(13)+;
							   "LTP saturation is no more viewed as a local synapse related phenomenon"+CHR(13)+;
							   "but as a whole cell phenomenon : the metabolic resources put a limit on the amount of LTP the cell can maintain."+CHR(13)+;
							   "Programmatically it is implemented by having a decline in terminal connection chance at the NON level"+;
							   " when LTP in the NON goes up."
	ENDCASE
	RETURN
	
	PROCEDURE Click(cCap)
	cCap=this.Caption
	DO CASE
	CASE "CS1"$cCap
		this.Caption=IIF(this.Caption="CS1 ON","CS1 OFF","CS1 ON")
		this.ForeColor=IIF(this.Caption="CS1 ON",pnRood,pnWit)
	CASE "CS2"$cCap
		this.Caption=IIF(this.Caption="CS2 ON","CS2 OFF","CS2 ON")
		this.ForeColor=IIF(this.Caption="CS2 ON",pnBlauw,pnWit)
	CASE "CS2"$cCap
		this.Caption=IIF(this.Caption="CS2 ON","CS2 OFF","CS2 ON")
	CASE "INTERMIXED"$this.Tag
		this.Caption="COMPOUNDED"
		this.Tag=this.Caption
		thisform.SG_SP3.Value=0
	CASE "COMPOUNDED"$this.Tag
		this.Caption="INTERMIXED"
		this.Tag=this.Caption
		IF thisform.SG_SP3.Value=0
			thisform.SG_SP3.Value=.1
		ENDIF
	CASE "TRACE"$cCap
		this.Caption=IIF(this.Caption="TRACE ON","TRACE OFF","TRACE ON")
	CASE "BACKGROUND"$cCap
		this.Caption=IIF(this.Caption="BACKGROUND ON","BACKGROUND OFF","BACKGROUND ON")
	CASE "METAB"$cCap
		this.Caption=IIF(this.Caption="METAB.BRAKE ON","METAB.BRAKE OFF","METAB.BRAKE ON")
	ENDCASE
	IF "ON"$thisform.SG_CBU1.Caption AND "ON"$thisform.SG_CBU2.Caption
		thisform.SG_CBU3.Enabled=.T.
		thisform.SG_CBU3.Caption=thisform.SG_CBU3.Tag
	ELSE
		thisform.SG_CBU3.Enabled=.F.
		thisform.SG_CBU3.Caption='---'
	ENDIF
	RETURN
	
ENDDEFINE
	
DEFINE CLASS SG_CBD AS LABEL 
	FontBold			= .T.
	Top				= 20
	Height			= 20
	Visible			= .T.
	FontSize			= 8
	Alignment		= 2
	BorderStyle		= 1

	PROCEDURE Init(nMax,	nX,cTTT)
	nX=VAL(RIGHT(this.Name,1))
	this.Width=(pnW/2)/nMax
	this.Left=(nX-1)*this.Width
	this.Caption=STREXTRACT(",RUN,,ABORT,",',',',',nX)
	this.BackColor=thisform.BackColor
	DO CASE
	CASE nX=2
		this.ToolTipText="Interrupts the run, click 'CONTINUE' to resume where it was halted."+CHR(13)+;
							  "You can use the 'run steps' setting to interrupt automatically after x steps."
	CASE nX=3
		this.ToolTipText="Aborts the run, click 'RUN' to restart."
	ENDCASE
	RETURN
	
	PROCEDURE MouseDown
	LPARAMETERS nButton, nShift, nXCoord, nYCoord,	cCap
	thisform.SetAll('ForeColor',pnZwart,'SG_CBD')
	cCap=this.Caption
	STORE .F. TO plRun,plAbort
	DO CASE
	CASE cCap="RUN"
		thisform.SetAll("Enabled",.F.,"SG_SP")
		thisform.SG_CBD2.Caption="STOP"
		plRun=.T.
		thisform.Cls
		IF thisform.SG_SP10.Value=0
			thisform.DORUN(.F.)
		ELSE
			pcCMD=LTRIM(STR(thisform.SG_SP10.Value))
			thisform.DEMO
		ENDIF
	CASE cCap="STOP"
		plStop=.T.
		thisform.SG_CBD1.Caption="CONTINUE"
	CASE cCap="CONTINUE"
		plRun=.T.
		thisform.DORUN(.T.)
	CASE cCap="ABORT"
		thisform.SetAll("Enabled",.T.,"SG_SP")
		plAbort=.T.
		thisform.SG_CBD1.Caption="RUN"
	ENDCASE
	RETURN
	
ENDDEFINE

DEFINE CLASS SG_SSLB AS LABEL
	FontBold		= .T.
	FontName		= "Courier New"
	FontSize		= 8
	Height			= 200
	Top				= 300
	Alignment		= 2
	
ENDDEFINE

DEFINE CLASS SG_SPLB AS COMMANDBUTTON
	FontBold			= .T.
	Height			= 30
	Visible			= .T.
	FontSize			= 6
	Alignment		= 2
	WordWrap			= .T.
	Top				= pnH-30*2
	BackColor		= pnWit
	
	PROCEDURE Init(nMax,	nX)
	nX=VAL(SUBSTR(this.Name,8))
	this.Width=(pnW/2)/nMax
	this.Left=(nX-1)*this.Width
	this.Caption=STREXTRACT(",NON quantity,LTP gain,LTD gain,CR (US brake) from,LTP brake from,Random factor,Background noise,Term. conn. chance one over x,STOP limit,Demo,Run x steps and interrupt,",',',',',nX)
	DO CASE
	CASE nX=1
		this.ToolTipText="Sets the number of displayed 'nanoloops' (NONs, PuCs ...) to x."
	CASE nX=2
		this.ToolTipText="A lower x value prolongs the run, showing a more detailed time course."
	CASE nX=3
		this.ToolTipText="Without LTD (x=0) there is no segregation."+;
							  " A high LTD gain speeds up segregation, but then 'double peaks' barely get a chance to appear."
	CASE nX=4
		this.ToolTipText="At this value of SUMSS (the active part) the US starts to be subdued by an upcoming CR."+CHR(13)+;
							  "When x is set low a long period of double peaks appears, if set high they may not appear at all."
	CASE nX=5
		this.ToolTipText="At x % of max LTP (10), LTP increase starts to slow down."+CHR(13)+;
							  "In 'single view' (at the synapse) it takes in account only the ACTIVE synapse."+CHR(13)+;
							  "In 'population view' it is interpreted that metabolic resources start to fall short to sustain the required LTP level cell wide,"+CHR(13)+;
							  "and hence (when 'metab. brake is ON') the calculation is based on the sum of all SSs (active and nonactive)."
	CASE nX=6
		this.ToolTipText="The random factor for LTP co-determines the speed of segregation : when x=0 no segregation occurs."
	CASE nX=7
		this.ToolTipText="Sets the % of background noise (here simulated by low frequency activation of the inactive competing CS)."
	CASE nX=8
		this.ToolTipText=	"Sets the chance for terminals to connect to NONs at the beginning of the run,"+CHR(13)+;
								"before the metabolic brake and declining US strength step in to lower it."+CHR(13)+;
								"Read the chance as 1/x at each step for each terminal."+CHR(13)+;
								"Keeping the chances high (x=1) raises the probability for double connections"+;
								" - needed to have an initial 'double peak phenomenon'."
	CASE nX=9
		this.ToolTipText="Ends the run when x% of maximum SumSS (the CR is a function of it) is reached."+CHR(13)+;
							  "Set at 100% to keep a run going on indefinitely."
	CASE nX=10
		this.ToolTipText="Sets the demo values for demo x . Move the cursor over the up- or downclick button to see a description of the demo."
	CASE nX=11
		this.ToolTipText="Interrupts the run every x steps, click on CONTINUE to resume."
	ENDCASE
	RETURN
	
ENDDEFINE

DEFINE CLASS SG_SP AS SPINNER
	FontBold				= .T.
	Height				= 30
	Visible				= .T.
	FontSize				= 7

	PROCEDURE Init(nMax,	nX,cX)
	nX=VAL(SUBSTR(this.Name,6))
	this.Width=(pnW/2)/nMax
	cX=LTRIM(STR(nX))
	this.Top=pnH-30
	this.ZOrder(1)
	this.Left=thisform.SG_SPLB&cX..Left

	&&									 NONQTY		LTP			LTD		CR_TH		LTP_BR_CR	RAND			BGN		Inichance	STOPLIM		Demo nr	RunSteps
	this.SpinnerLowValue= ICASE(nX=1,6,		nX=2,0.1,	nX=3,0.0,nX=4,0,	nX=5,0,		nX=6,0.0,	nX=7,0,	nX=8,0,		nX=9,10,		nX=10,0,	nX=11,0)
	this.SpinnerHighValue=ICASE(nX=1,100,	nX=2,5,		nX=3,5,	nX=4,99,	nX=5,100,	nX=6,10.0,	nX=7,100,nX=8,5000,	nX=9,100,	nX=10,20,nX=11,500)
	this.Increment=		 ICASE(nX=1,2,		nX=2,0.1,	nX=3,0.1,nX=4,1,	nX=5,1,		nX=6,0.1,	nX=7,1,	nX=8,10,		nX=9,1,		nX=10,1,	nX=11,10)
	this.Value=				 ICASE(nX=1,10,	nX=2,.1,		nX=3,.1,	nX=4,30,	nX=5,70,		nX=6,5.0,	nX=7,0,	nX=8,1,		nX=9,90,		nX=10,0,	nX=11,0)
	
	this.ControlSource=FIELD(nX)
	RETURN
	
	PROCEDURE Valid(nX,cX)
	nX=VAL(SUBSTR(this.Name,6))
	IF nX<=AFIELDS(AF)
		cX="SGM."+FIELD(nX)
		REPLACE &cX WITH this.Value
	ENDIF
	RETURN(.T.)
	
	PROCEDURE UpClick(nX,cX)
	nX=VAL(SUBSTR(this.Name,6))
	IF nX=AFIELDS(AF)+1
		thisform.SG_CBD1.Caption="RUN"
		cX=FIELD(nX)
		pcCMD=LTRIM(STR(this.Value))
		this.TTText(this.Value)
		thisform.DEMO(.T.)
	ENDIF
	RETURN

	PROCEDURE TTText(nCMD)
	DO CASE
		CASE nCMD=1
		 this.ToolTipText="Presentation of demo components."
		CASE nCMD=2
		 this.ToolTipText="Showing thickening lines."
		CASE nCMD=3
		 this.ToolTipText="Showing Gauss curves."
		CASE nCMD=4
		 this.ToolTipText="Complete run, intermixed, trace off, showing the segregation process."
		CASE nCMD=5
		 this.ToolTipText="Trace divergence demo with 10 NONs, random function enabled."
		CASE nCMD=6
		 this.ToolTipText="Trace divergence demo with 10 NONs, random function disabled."
		CASE nCMD=7
		 this.ToolTipText="'Transfer training' CS1->CS2->CS1 with M-BRAKE OFF."
		CASE nCMD=8
		 this.ToolTipText="'Transfer training' CS1->CS2 with M-BRAKE ON."
		CASE nCMD=9
		 this.ToolTipText="CS1 CS2 INTERMIXED with M-BRAKE ON."
		CASE nCMD=10
		 this.ToolTipText="'Transfer training' CS1->CS2->CS1 with M-BRAKE ON,"+CHR(13)+;
		 						"running longer to watch 'erosion' of CS1,"+CHR(13)+;
		 						"and quick resurgence of CS1 when activated again."
		CASE nCMD=11
		 this.ToolTipText="'Transfer training' CS1->CS2->CS1 with M-BRAKE ON AND background noise."
		CASE nCMD=12
		 this.ToolTipText="Interactive mode."
		CASE nCMD=13
		 this.ToolTipText="CS1 CS2 COMPOUNDED with M-BRAKE ON AND Background noise."
		CASE nCMD=14
		 this.ToolTipText="Blocking of CS1 after full training with CS2."
	ENDCASE
	RETURN

	PROCEDURE DownClick
	this.UpClick
	RETURN

ENDDEFINE

PROCEDURE INITCOLOR
pnZwart=					RGB(0,0,0)
pnLichtGrijs=			RGB(192,192,192)
pnGrijs=					RGB(128,128,128)
pnDonkerGrijs=			RGB(32,32,32)
pnWit=					RGB(255,255,255)

pnLichtRood=			RGB(255,128,128)
pnRood=					RGB(255,0,0)
pnDonkerRood=			RGB(128,0,0)
pnLichtGroen=			RGB(128,255,128)
pnGroen=					RGB(0,255,0)
pnDonkerGroen=			RGB(0,128,0)

pnLichtBlauw=				RGB(64,64,255)
pnBlauw=					RGB(0,0,255)
pnDonkerBlauw=			RGB(0,0,128)
pnGeel=					RGB(255,255,0)
pnLichtGeel=			RGB(255,255,128)
pnHalfDonkerGeel=		RGB(255,128,0)
pnDonkerGeel=			RGB(128,128,0)

pnCyaan=					RGB(0,255,255)
pnLichtCyaan=			RGB(128,255,255)
pnHalfDonkerCyaan=	RGB(0,128,255)
pnDonkerCyaan=			RGB(0,128,128)
pnMagenta=				RGB(255,0,255)
pnLichtMagenta=		RGB(255,128,255)

RETURN

	PROCEDURE DING
   SET BELL TO LEFT(pcDIR,2)+'\WINDOWS\MEDIA\WINDOWS DING.WAV',1 && !!!
   ?? CHR(7)
   SET BELL TO
   RETURN
   
	PROCEDURE CHORD
   SET BELL TO LEFT(pcDIR,2)+'\WINDOWS\MEDIA\CHORD.WAV',1 && !!!
   ?? CHR(7),CHR(7)
   SET BELL TO
   RETURN
   
