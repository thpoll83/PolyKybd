EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 2 3
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Sheet
S 5150 2350 1350 2000
U 605ED310
F0 "sheet605ED2EB" 50
F1 "SSD1306_TO_SPI.sch" 50
F2 "SDIN" I R 6500 3600 50 
F3 "SCLK" I L 5150 3600 50 
F4 "D-C" I L 5150 3500 50 
F5 "CS" I R 6500 3800 50 
F6 "RESET" I R 6500 3500 50 
F7 "LED_DIN" I R 6500 3150 50 
F8 "LED_DOUT" I R 6500 3250 50 
F9 "GND" I R 6500 2450 50 
F10 "3V3" I R 6500 2800 50 
F11 "4V2" I R 6500 2550 50 
F12 "5V" I R 6500 2900 50 
F13 "KeyRow" I R 6500 4150 50 
F14 "KeyCol" I R 6500 4250 50 
$EndSheet
$Comp
L Connector_Generic:Conn_01x09 J4
U 1 1 60DD874F
P 8100 1900
F 0 "J4" H 8180 1937 50  0000 L CNN
F 1 "EastFront" H 8180 1846 50  0000 L CNN
F 2 "poly_kb:AtomConnect2" H 8180 1755 50  0000 L CNN
F 3 "~" H 8100 1900 50  0001 C CNN
F 4 "" H 8100 1900 50  0001 C CNN "LCSC"
	1    8100 1900
	1    0    0    -1  
$EndComp
Wire Wire Line
	6500 3150 7400 3150
Wire Wire Line
	6500 3600 6900 3600
Wire Wire Line
	6900 3600 6900 3550
Wire Wire Line
	6500 3500 6950 3500
Wire Wire Line
	6950 3500 6950 3450
$Comp
L Connector_Generic:Conn_01x09 J3
U 1 1 6132B688
P 4350 1900
F 0 "J3" H 4430 1937 50  0000 L CNN
F 1 "WestFront" H 4430 1846 50  0000 L CNN
F 2 "poly_kb:AtomConnect2" H 4430 1755 50  0000 L CNN
F 3 "~" H 4350 1900 50  0001 C CNN
F 4 "" H 4350 1900 50  0001 C CNN "LCSC"
	1    4350 1900
	-1   0    0    -1  
$EndComp
Wire Wire Line
	4550 1500 6950 1500
Connection ~ 6950 1500
Wire Wire Line
	6950 1500 7900 1500
Wire Wire Line
	6500 2800 7050 2800
Wire Wire Line
	7050 2800 7050 1600
Wire Wire Line
	7050 1600 7900 1600
Wire Wire Line
	7050 1600 4550 1600
Connection ~ 7050 1600
Wire Wire Line
	7150 1700 7900 1700
Wire Wire Line
	4550 1700 7150 1700
Connection ~ 7150 1700
Wire Wire Line
	7400 3150 7400 1800
Wire Wire Line
	6500 3250 7250 3250
Wire Wire Line
	7700 3450 7700 1900
Wire Wire Line
	7700 1900 7900 1900
Wire Wire Line
	6950 3450 7700 3450
Wire Wire Line
	7700 1900 4550 1900
Connection ~ 7700 1900
Wire Wire Line
	7800 3550 7800 2000
Wire Wire Line
	7800 2000 7900 2000
Wire Wire Line
	7800 2000 4550 2000
Connection ~ 7800 2000
Wire Wire Line
	6900 3550 7800 3550
Wire Wire Line
	5150 3500 4850 3500
Wire Wire Line
	4850 3500 4850 2100
Wire Wire Line
	4850 2100 4550 2100
Wire Wire Line
	4850 2100 7900 2100
Connection ~ 4850 2100
Wire Wire Line
	5150 3600 4700 3600
Wire Wire Line
	4700 3600 4700 2200
Wire Wire Line
	4700 2200 4550 2200
Wire Wire Line
	4700 2200 7900 2200
Connection ~ 4700 2200
$Comp
L Connector_Generic:Conn_01x09 J6
U 1 1 613EFBA3
P 8100 5250
F 0 "J6" H 8180 5287 50  0000 L CNN
F 1 "EastBack" H 8180 5196 50  0000 L CNN
F 2 "poly_kb:AtomConnect2" H 8180 5105 50  0000 L CNN
F 3 "~" H 8100 5250 50  0001 C CNN
F 4 "" H 8100 5250 50  0001 C CNN "LCSC"
	1    8100 5250
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_01x10 J5
U 1 1 613F0D03
P 4400 5250
F 0 "J5" H 4480 5287 50  0000 L CNN
F 1 "WestBack" H 4480 5196 50  0000 L CNN
F 2 "poly_kb:AtomConnectCS" H 4480 5105 50  0000 L CNN
F 3 "~" H 4400 5250 50  0001 C CNN
F 4 "" H 4400 5250 50  0001 C CNN "LCSC"
	1    4400 5250
	-1   0    0    -1  
$EndComp
Wire Wire Line
	4600 4950 4900 4950
Wire Wire Line
	4600 5150 5200 5150
Wire Wire Line
	6500 3800 7200 3800
Wire Wire Line
	7200 3800 7200 5750
Wire Wire Line
	7900 4150 7900 2300
Wire Wire Line
	4550 2300 7900 2300
Connection ~ 7900 2300
Wire Wire Line
	6500 4150 7900 4150
Wire Wire Line
	6700 2450 6700 4850
Wire Wire Line
	6700 4850 7900 4850
Connection ~ 6700 4850
Wire Wire Line
	6500 2450 6700 2450
$Comp
L Connector_Generic:Conn_01x01 J2
U 1 1 61409CF2
P 6050 950
F 0 "J2" V 6014 762 50  0000 R CNN
F 1 "North" V 5923 762 50  0000 R CNN
F 2 "poly_kb:TestPoin_1.5x1.5mm_Drill0.7mm" H 6050 950 50  0001 C CNN
F 3 "~" H 6050 950 50  0001 C CNN
	1    6050 950 
	0    -1   -1   0   
$EndComp
Wire Wire Line
	6050 1250 6050 1150
$Comp
L Connector_Generic:Conn_01x01 J7
U 1 1 61410C7E
P 6300 6700
F 0 "J7" V 6172 6880 50  0000 L CNN
F 1 "South" V 6263 6880 50  0000 L CNN
F 2 "poly_kb:TestPoin_1.5x1.5mm_Drill0.7mm" H 6300 6700 50  0001 C CNN
F 3 "~" H 6300 6700 50  0001 C CNN
	1    6300 6700
	0    1    1    0   
$EndComp
Wire Wire Line
	9150 6300 6300 6300
Wire Wire Line
	6300 6300 6300 6500
Text GLabel 4900 4900 1    50   Input ~ 0
CS1
Text GLabel 5050 5000 1    50   Input ~ 0
CS2
Text GLabel 5200 5100 1    50   Input ~ 0
CS3
Text GLabel 4900 5200 1    50   Input ~ 0
CS4
Text GLabel 5050 5300 1    50   Input ~ 0
CS5
Text GLabel 5200 5400 1    50   Input ~ 0
CS6
Text GLabel 4900 5500 1    50   Input ~ 0
CS7
Text GLabel 5050 5600 1    50   Input ~ 0
CS8
Wire Wire Line
	6950 2900 6500 2900
Wire Wire Line
	6950 1500 6950 2900
Wire Wire Line
	7150 2550 7150 1700
Wire Wire Line
	6500 2550 7150 2550
Wire Wire Line
	7400 1800 7900 1800
Wire Wire Line
	4550 1800 7250 1800
Wire Wire Line
	7250 1800 7250 3250
Wire Wire Line
	4600 4850 6700 4850
$Comp
L Connector_Generic:Conn_01x01 J8
U 1 1 61441F3E
P 6750 950
F 0 "J8" V 6714 762 50  0000 R CNN
F 1 "North2" V 6623 762 50  0000 R CNN
F 2 "poly_kb:TestPoin_1.5x1.5mm_Drill0.7mm" H 6750 950 50  0001 C CNN
F 3 "~" H 6750 950 50  0001 C CNN
	1    6750 950 
	0    -1   -1   0   
$EndComp
Wire Wire Line
	6750 1250 6750 1150
$Comp
L Connector_Generic:Conn_01x01 J9
U 1 1 61444659
P 5700 6700
F 0 "J9" V 5572 6880 50  0000 L CNN
F 1 "South2" V 5663 6880 50  0000 L CNN
F 2 "poly_kb:TestPoin_1.5x1.5mm_Drill0.7mm" H 5700 6700 50  0001 C CNN
F 3 "~" H 5700 6700 50  0001 C CNN
	1    5700 6700
	0    1    1    0   
$EndComp
Wire Wire Line
	6300 6300 5700 6300
Wire Wire Line
	5700 6300 5700 6500
Connection ~ 6300 6300
Wire Wire Line
	6050 1250 6750 1250
Connection ~ 6750 1250
Wire Wire Line
	6750 1250 9150 1250
Wire Wire Line
	9150 1250 9150 4250
Wire Wire Line
	6500 4250 9150 4250
Connection ~ 9150 4250
Wire Wire Line
	9150 4250 9150 6300
Wire Wire Line
	4600 5550 4900 5550
Wire Wire Line
	4600 5650 5050 5650
Wire Wire Line
	4600 5450 5200 5450
Wire Wire Line
	4900 4900 4900 4950
Connection ~ 4900 4950
Wire Wire Line
	5050 5000 5050 5050
Connection ~ 5050 5050
Wire Wire Line
	5050 5050 4600 5050
Wire Wire Line
	5200 5100 5200 5150
Connection ~ 5200 5150
Wire Wire Line
	5200 5400 5200 5450
Connection ~ 5200 5450
Wire Wire Line
	5050 5600 5050 5650
Connection ~ 5050 5650
Wire Wire Line
	4900 5500 4900 5550
Connection ~ 4900 5550
Wire Wire Line
	4900 4950 7900 4950
Wire Wire Line
	5050 5050 7900 5050
Wire Wire Line
	5200 5150 7900 5150
Wire Wire Line
	4600 5250 4900 5250
Wire Wire Line
	4600 5350 5050 5350
Wire Wire Line
	5200 5450 7900 5450
Wire Wire Line
	4900 5550 7900 5550
Wire Wire Line
	5050 5650 7900 5650
Wire Wire Line
	4600 5750 7200 5750
Wire Wire Line
	4900 5200 4900 5250
Connection ~ 4900 5250
Wire Wire Line
	4900 5250 7900 5250
Wire Wire Line
	5050 5300 5050 5350
Connection ~ 5050 5350
Wire Wire Line
	5050 5350 7900 5350
$EndSCHEMATC
