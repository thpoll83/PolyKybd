EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L 74xx:74HCT595 U1
U 1 1 61939815
P 10100 2050
F 0 "U1" V 10054 2694 50  0000 L CNN
F 1 "74HCT595" V 10150 1850 50  0000 L CNN
F 2 "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm" H 10100 2050 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf" H 10100 2050 50  0001 C CNN
	1    10100 2050
	0    1    1    0   
$EndComp
Text GLabel 10500 1650 1    50   Input ~ 0
SHIFTR_DATA
Text GLabel 10300 1650 1    50   Input ~ 0
SHIFTR_CLK
Text GLabel 10200 1650 1    50   Input ~ 0
SHIFTR_RST
Text GLabel 10000 1650 1    50   Input ~ 0
SHIFTR_LATCH_CLK
$Comp
L power:GND #PWR011
U 1 1 6193C27C
P 9400 2050
F 0 "#PWR011" H 9400 1800 50  0001 C CNN
F 1 "GND" V 9405 1922 50  0000 R CNN
F 2 "" H 9400 2050 50  0001 C CNN
F 3 "" H 9400 2050 50  0001 C CNN
	1    9400 2050
	0    1    1    0   
$EndComp
$Comp
L 74xx:74HCT595 U2
U 1 1 6193DE17
P 8050 2050
F 0 "U2" V 8004 2694 50  0000 L CNN
F 1 "74HCT595" V 8100 1900 50  0000 L CNN
F 2 "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm" H 8050 2050 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf" H 8050 2050 50  0001 C CNN
	1    8050 2050
	0    1    1    0   
$EndComp
Text GLabel 8250 1650 1    50   Input ~ 0
SHIFTR_CLK
Text GLabel 8150 1650 1    50   Input ~ 0
SHIFTR_RST
Text GLabel 7950 1650 1    50   Input ~ 0
SHIFTR_LATCH_CLK
$Comp
L power:GND #PWR09
U 1 1 6193DE22
P 7350 2050
F 0 "#PWR09" H 7350 1800 50  0001 C CNN
F 1 "GND" V 7355 1922 50  0000 R CNN
F 2 "" H 7350 2050 50  0001 C CNN
F 3 "" H 7350 2050 50  0001 C CNN
	1    7350 2050
	0    1    1    0   
$EndComp
Wire Wire Line
	9600 2450 9100 2450
Wire Wire Line
	9100 2450 9100 1650
Wire Wire Line
	9100 1650 8450 1650
$Comp
L power:+3.3V #PWR010
U 1 1 6193E33F
P 8650 2050
F 0 "#PWR010" H 8650 1900 50  0001 C CNN
F 1 "+3.3V" V 8665 2178 50  0000 L CNN
F 2 "" H 8650 2050 50  0001 C CNN
F 3 "" H 8650 2050 50  0001 C CNN
	1    8650 2050
	0    1    1    0   
$EndComp
$Comp
L power:+3.3V #PWR012
U 1 1 6193F72D
P 10700 2050
F 0 "#PWR012" H 10700 1900 50  0001 C CNN
F 1 "+3.3V" V 10715 2178 50  0000 L CNN
F 2 "" H 10700 2050 50  0001 C CNN
F 3 "" H 10700 2050 50  0001 C CNN
	1    10700 2050
	0    1    1    0   
$EndComp
$Comp
L 74xx:74HCT595 U3
U 1 1 61940E33
P 5850 2050
F 0 "U3" V 5804 2694 50  0000 L CNN
F 1 "74HCT595" V 5900 1900 50  0000 L CNN
F 2 "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm" H 5850 2050 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf" H 5850 2050 50  0001 C CNN
	1    5850 2050
	0    1    1    0   
$EndComp
Text GLabel 6050 1650 1    50   Input ~ 0
SHIFTR_CLK
Text GLabel 5950 1650 1    50   Input ~ 0
SHIFTR_RST
Text GLabel 5750 1650 1    50   Input ~ 0
SHIFTR_LATCH_CLK
$Comp
L power:GND #PWR07
U 1 1 61940E3D
P 5150 2050
F 0 "#PWR07" H 5150 1800 50  0001 C CNN
F 1 "GND" V 5155 1922 50  0000 R CNN
F 2 "" H 5150 2050 50  0001 C CNN
F 3 "" H 5150 2050 50  0001 C CNN
	1    5150 2050
	0    1    1    0   
$EndComp
$Comp
L power:+3.3V #PWR08
U 1 1 61940E44
P 6450 2050
F 0 "#PWR08" H 6450 1900 50  0001 C CNN
F 1 "+3.3V" V 6465 2178 50  0000 L CNN
F 2 "" H 6450 2050 50  0001 C CNN
F 3 "" H 6450 2050 50  0001 C CNN
	1    6450 2050
	0    1    1    0   
$EndComp
Wire Wire Line
	7550 2450 7000 2450
Wire Wire Line
	7000 2450 7000 1650
Wire Wire Line
	6250 1650 7000 1650
$Comp
L Connector_Generic:Conn_01x09 J2
U 1 1 61941D6F
P 10600 3200
F 0 "J2" H 10680 3242 50  0000 L CNN
F 1 "Conn_01x09" H 10680 3151 50  0000 L CNN
F 2 "poly_kb:AtomConnect2" H 10600 3200 50  0001 C CNN
F 3 "~" H 10600 3200 50  0001 C CNN
	1    10600 3200
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_01x09 J1
U 1 1 6194447A
P 9550 3200
F 0 "J1" H 9468 3817 50  0000 C CNN
F 1 "Conn_01x09" H 9468 3726 50  0000 C CNN
F 2 "poly_kb:AtomConnect2" H 9550 3200 50  0001 C CNN
F 3 "~" H 9550 3200 50  0001 C CNN
	1    9550 3200
	-1   0    0    -1  
$EndComp
Text GLabel 10400 2800 0    50   Input ~ 0
VLED
Text GLabel 10400 3000 0    50   Input ~ 0
VBAT
Text GLabel 10400 3800 3    50   Input ~ 0
LedIn1
Text GLabel 10400 3200 0    50   Input ~ 0
RST
Text GLabel 10400 3300 0    50   Input ~ 0
SI
Text GLabel 10400 3400 0    50   Input ~ 0
D\C
Text GLabel 10400 3500 0    50   Input ~ 0
CLK
Text GLabel 10400 3600 0    50   Input ~ 0
r1
$Comp
L power:GND #PWR018
U 1 1 61946FF2
P 9750 2800
F 0 "#PWR018" H 9750 2550 50  0001 C CNN
F 1 "GND" V 9755 2672 50  0000 R CNN
F 2 "" H 9750 2800 50  0001 C CNN
F 3 "" H 9750 2800 50  0001 C CNN
	1    9750 2800
	0    -1   -1   0   
$EndComp
Text GLabel 9750 2900 2    50   Input ~ 0
1
Text GLabel 9750 3000 2    50   Input ~ 0
2
Text GLabel 9750 3100 2    50   Input ~ 0
3
Text GLabel 9750 3200 2    50   Input ~ 0
4
Text GLabel 9750 3300 2    50   Input ~ 0
5
Text GLabel 9750 3400 2    50   Input ~ 0
6
Text GLabel 9750 3500 2    50   Input ~ 0
7
Text GLabel 9750 3600 2    50   Input ~ 0
8
Text GLabel 10500 2450 3    50   Input ~ 0
1
Text GLabel 10400 2450 3    50   Input ~ 0
2
Text GLabel 10300 2450 3    50   Input ~ 0
3
Text GLabel 10200 2450 3    50   Input ~ 0
4
Text GLabel 10100 2450 3    50   Input ~ 0
5
Text GLabel 10000 2450 3    50   Input ~ 0
6
Text GLabel 9900 2450 3    50   Input ~ 0
7
Text GLabel 9800 2450 3    50   Input ~ 0
8
Text GLabel 600  6100 3    50   Input ~ 0
SHIFTR_OUT
$Comp
L 74xx:74HCT595 U4
U 1 1 61950BC7
P 5800 5700
F 0 "U4" V 5754 6344 50  0000 L CNN
F 1 "74HCT595" V 5850 5500 50  0000 L CNN
F 2 "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm" H 5800 5700 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf" H 5800 5700 50  0001 C CNN
	1    5800 5700
	0    1    1    0   
$EndComp
Text GLabel 6000 5300 1    50   Input ~ 0
SHIFTR_CLK
Text GLabel 5900 5300 1    50   Input ~ 0
SHIFTR_RST
Text GLabel 5700 5300 1    50   Input ~ 0
SHIFTR_LATCH_CLK
$Comp
L power:GND #PWR05
U 1 1 61950BD2
P 5100 5700
F 0 "#PWR05" H 5100 5450 50  0001 C CNN
F 1 "GND" V 5105 5572 50  0000 R CNN
F 2 "" H 5100 5700 50  0001 C CNN
F 3 "" H 5100 5700 50  0001 C CNN
	1    5100 5700
	0    1    1    0   
$EndComp
$Comp
L 74xx:74HCT595 U5
U 1 1 61950BD8
P 3750 5700
F 0 "U5" V 3704 6344 50  0000 L CNN
F 1 "74HCT595" V 3800 5550 50  0000 L CNN
F 2 "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm" H 3750 5700 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf" H 3750 5700 50  0001 C CNN
	1    3750 5700
	0    1    1    0   
$EndComp
Text GLabel 3950 5300 1    50   Input ~ 0
SHIFTR_CLK
Text GLabel 3850 5300 1    50   Input ~ 0
SHIFTR_RST
Text GLabel 3650 5300 1    50   Input ~ 0
SHIFTR_LATCH_CLK
$Comp
L power:GND #PWR03
U 1 1 61950BE2
P 3050 5700
F 0 "#PWR03" H 3050 5450 50  0001 C CNN
F 1 "GND" V 3055 5572 50  0000 R CNN
F 2 "" H 3050 5700 50  0001 C CNN
F 3 "" H 3050 5700 50  0001 C CNN
	1    3050 5700
	0    1    1    0   
$EndComp
Wire Wire Line
	5300 6100 4800 6100
Wire Wire Line
	4800 6100 4800 5300
Wire Wire Line
	4800 5300 4150 5300
$Comp
L power:+3.3V #PWR04
U 1 1 61950BEB
P 4350 5700
F 0 "#PWR04" H 4350 5550 50  0001 C CNN
F 1 "+3.3V" V 4365 5828 50  0000 L CNN
F 2 "" H 4350 5700 50  0001 C CNN
F 3 "" H 4350 5700 50  0001 C CNN
	1    4350 5700
	0    1    1    0   
$EndComp
$Comp
L power:+3.3V #PWR06
U 1 1 61950BF1
P 6400 5700
F 0 "#PWR06" H 6400 5550 50  0001 C CNN
F 1 "+3.3V" V 6415 5828 50  0000 L CNN
F 2 "" H 6400 5700 50  0001 C CNN
F 3 "" H 6400 5700 50  0001 C CNN
	1    6400 5700
	0    1    1    0   
$EndComp
Text GLabel 1750 5300 1    50   Input ~ 0
SHIFTR_CLK
Text GLabel 1650 5300 1    50   Input ~ 0
SHIFTR_RST
Text GLabel 1450 5300 1    50   Input ~ 0
SHIFTR_LATCH_CLK
$Comp
L power:GND #PWR01
U 1 1 61950C01
P 850 5700
F 0 "#PWR01" H 850 5450 50  0001 C CNN
F 1 "GND" V 855 5572 50  0000 R CNN
F 2 "" H 850 5700 50  0001 C CNN
F 3 "" H 850 5700 50  0001 C CNN
	1    850  5700
	0    1    1    0   
$EndComp
$Comp
L power:+3.3V #PWR02
U 1 1 61950C07
P 2150 5700
F 0 "#PWR02" H 2150 5550 50  0001 C CNN
F 1 "+3.3V" V 2165 5828 50  0000 L CNN
F 2 "" H 2150 5700 50  0001 C CNN
F 3 "" H 2150 5700 50  0001 C CNN
	1    2150 5700
	0    1    1    0   
$EndComp
Wire Wire Line
	3250 6100 2700 6100
Wire Wire Line
	2700 6100 2700 5300
Wire Wire Line
	1950 5300 2700 5300
$Comp
L Connector_Generic:Conn_01x09 J4
U 1 1 619545FE
P 8500 3150
F 0 "J4" H 8580 3192 50  0000 L CNN
F 1 "Conn_01x09" H 8580 3101 50  0000 L CNN
F 2 "poly_kb:AtomConnect2" H 8500 3150 50  0001 C CNN
F 3 "~" H 8500 3150 50  0001 C CNN
	1    8500 3150
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_01x09 J3
U 1 1 61954604
P 7450 3150
F 0 "J3" H 7368 3767 50  0000 C CNN
F 1 "Conn_01x09" H 7368 3676 50  0000 C CNN
F 2 "poly_kb:AtomConnect2" H 7450 3150 50  0001 C CNN
F 3 "~" H 7450 3150 50  0001 C CNN
	1    7450 3150
	-1   0    0    -1  
$EndComp
Text GLabel 8300 2750 0    50   Input ~ 0
VLED
Text GLabel 8300 2950 0    50   Input ~ 0
VBAT
Text GLabel 8300 3150 0    50   Input ~ 0
RST
Text GLabel 8300 3250 0    50   Input ~ 0
SI
Text GLabel 8300 3350 0    50   Input ~ 0
D\C
Text GLabel 8300 3450 0    50   Input ~ 0
CLK
Text GLabel 8300 3550 0    50   Input ~ 0
r2
$Comp
L power:GND #PWR017
U 1 1 61954618
P 7650 2750
F 0 "#PWR017" H 7650 2500 50  0001 C CNN
F 1 "GND" V 7655 2622 50  0000 R CNN
F 2 "" H 7650 2750 50  0001 C CNN
F 3 "" H 7650 2750 50  0001 C CNN
	1    7650 2750
	0    -1   -1   0   
$EndComp
Text GLabel 7650 2850 2    50   Input ~ 0
9
Text GLabel 7650 2950 2    50   Input ~ 0
10
Text GLabel 7650 3050 2    50   Input ~ 0
11
Text GLabel 7650 3150 2    50   Input ~ 0
12
Text GLabel 7650 3250 2    50   Input ~ 0
13
Text GLabel 7650 3350 2    50   Input ~ 0
14
Text GLabel 7650 3450 2    50   Input ~ 0
15
Text GLabel 7650 3550 2    50   Input ~ 0
16
$Comp
L Connector_Generic:Conn_01x09 J6
U 1 1 619567DC
P 6300 3150
F 0 "J6" H 6380 3192 50  0000 L CNN
F 1 "Conn_01x09" H 6380 3101 50  0000 L CNN
F 2 "poly_kb:AtomConnect2" H 6300 3150 50  0001 C CNN
F 3 "~" H 6300 3150 50  0001 C CNN
	1    6300 3150
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_01x09 J5
U 1 1 619567E2
P 5250 3150
F 0 "J5" H 5168 3767 50  0000 C CNN
F 1 "Conn_01x09" H 5168 3676 50  0000 C CNN
F 2 "poly_kb:AtomConnect2" H 5250 3150 50  0001 C CNN
F 3 "~" H 5250 3150 50  0001 C CNN
	1    5250 3150
	-1   0    0    -1  
$EndComp
Text GLabel 6100 2750 0    50   Input ~ 0
VLED
Text GLabel 6100 2950 0    50   Input ~ 0
VBAT
Text GLabel 6100 3150 0    50   Input ~ 0
RST
Text GLabel 6100 3250 0    50   Input ~ 0
SI
Text GLabel 6100 3350 0    50   Input ~ 0
D\C
Text GLabel 6100 3450 0    50   Input ~ 0
CLK
Text GLabel 6100 3550 0    50   Input ~ 0
r3
$Comp
L power:GND #PWR016
U 1 1 619567F6
P 5450 2750
F 0 "#PWR016" H 5450 2500 50  0001 C CNN
F 1 "GND" V 5455 2622 50  0000 R CNN
F 2 "" H 5450 2750 50  0001 C CNN
F 3 "" H 5450 2750 50  0001 C CNN
	1    5450 2750
	0    -1   -1   0   
$EndComp
Text GLabel 5450 2850 2    50   Input ~ 0
17
Text GLabel 5450 2950 2    50   Input ~ 0
18
Text GLabel 5450 3050 2    50   Input ~ 0
19
Text GLabel 5450 3150 2    50   Input ~ 0
20
Text GLabel 5450 3250 2    50   Input ~ 0
21
Text GLabel 5450 3350 2    50   Input ~ 0
22
Text GLabel 5450 3450 2    50   Input ~ 0
23
Text GLabel 5450 3550 2    50   Input ~ 0
24
$Comp
L Connector_Generic:Conn_01x09 J8
U 1 1 61957D26
P 6300 6800
F 0 "J8" H 6380 6842 50  0000 L CNN
F 1 "Conn_01x09" H 6380 6751 50  0000 L CNN
F 2 "poly_kb:AtomConnect2" H 6300 6800 50  0001 C CNN
F 3 "~" H 6300 6800 50  0001 C CNN
	1    6300 6800
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_01x09 J7
U 1 1 61957D2C
P 5250 6800
F 0 "J7" H 5168 7417 50  0000 C CNN
F 1 "Conn_01x09" H 5168 7326 50  0000 C CNN
F 2 "poly_kb:AtomConnect2" H 5250 6800 50  0001 C CNN
F 3 "~" H 5250 6800 50  0001 C CNN
	1    5250 6800
	-1   0    0    -1  
$EndComp
Text GLabel 6100 6400 0    50   Input ~ 0
VLED
Text GLabel 6100 6600 0    50   Input ~ 0
VBAT
Text GLabel 6100 6800 0    50   Input ~ 0
RST
Text GLabel 6100 6900 0    50   Input ~ 0
SI
Text GLabel 6100 7000 0    50   Input ~ 0
D\C
Text GLabel 6100 7100 0    50   Input ~ 0
CLK
Text GLabel 6100 7200 0    50   Input ~ 0
r4
$Comp
L power:GND #PWR015
U 1 1 61957D40
P 5450 6400
F 0 "#PWR015" H 5450 6150 50  0001 C CNN
F 1 "GND" V 5455 6272 50  0000 R CNN
F 2 "" H 5450 6400 50  0001 C CNN
F 3 "" H 5450 6400 50  0001 C CNN
	1    5450 6400
	0    -1   -1   0   
$EndComp
Text GLabel 5450 6500 2    50   Input ~ 0
25
Text GLabel 5450 6600 2    50   Input ~ 0
26
Text GLabel 5450 6700 2    50   Input ~ 0
27
Text GLabel 5450 6800 2    50   Input ~ 0
28
Text GLabel 5450 6900 2    50   Input ~ 0
29
Text GLabel 5450 7000 2    50   Input ~ 0
30
Text GLabel 5450 7100 2    50   Input ~ 0
31
Text GLabel 5450 7200 2    50   Input ~ 0
32
$Comp
L Connector_Generic:Conn_01x09 J10
U 1 1 61959444
P 4250 6800
F 0 "J10" H 4330 6842 50  0000 L CNN
F 1 "Conn_01x09" H 4330 6751 50  0000 L CNN
F 2 "poly_kb:AtomConnect2" H 4250 6800 50  0001 C CNN
F 3 "~" H 4250 6800 50  0001 C CNN
	1    4250 6800
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_01x09 J9
U 1 1 6195944A
P 3200 6800
F 0 "J9" H 3118 7417 50  0000 C CNN
F 1 "Conn_01x09" H 3118 7326 50  0000 C CNN
F 2 "poly_kb:AtomConnect2" H 3200 6800 50  0001 C CNN
F 3 "~" H 3200 6800 50  0001 C CNN
	1    3200 6800
	-1   0    0    -1  
$EndComp
Text GLabel 4050 6400 0    50   Input ~ 0
VLED
Text GLabel 4050 6600 0    50   Input ~ 0
VBAT
Text GLabel 4050 6800 0    50   Input ~ 0
RST
Text GLabel 4050 6900 0    50   Input ~ 0
SI
Text GLabel 4050 7000 0    50   Input ~ 0
D\C
Text GLabel 4050 7100 0    50   Input ~ 0
CLK
Text GLabel 4050 7200 0    50   Input ~ 0
r5
$Comp
L power:GND #PWR014
U 1 1 6195945E
P 3400 6400
F 0 "#PWR014" H 3400 6150 50  0001 C CNN
F 1 "GND" V 3405 6272 50  0000 R CNN
F 2 "" H 3400 6400 50  0001 C CNN
F 3 "" H 3400 6400 50  0001 C CNN
	1    3400 6400
	0    -1   -1   0   
$EndComp
Text GLabel 3400 6500 2    50   Input ~ 0
33
Text GLabel 3400 6600 2    50   Input ~ 0
34
Text GLabel 3400 6700 2    50   Input ~ 0
35
Text GLabel 3400 6800 2    50   Input ~ 0
36
Text GLabel 3400 6900 2    50   Input ~ 0
37
Text GLabel 3400 7000 2    50   Input ~ 0
38
Text GLabel 3400 7100 2    50   Input ~ 0
39
Text GLabel 3400 7200 2    50   Input ~ 0
40
$Comp
L Connector_Generic:Conn_01x09 J12
U 1 1 6195DBFE
P 2000 6800
F 0 "J12" H 2080 6842 50  0000 L CNN
F 1 "Conn_01x09" H 2080 6751 50  0000 L CNN
F 2 "poly_kb:AtomConnect2" H 2000 6800 50  0001 C CNN
F 3 "~" H 2000 6800 50  0001 C CNN
	1    2000 6800
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_01x09 J11
U 1 1 6195DC04
P 950 6800
F 0 "J11" H 868 7417 50  0000 C CNN
F 1 "Conn_01x09" H 868 7326 50  0000 C CNN
F 2 "poly_kb:AtomConnect2" H 950 6800 50  0001 C CNN
F 3 "~" H 950 6800 50  0001 C CNN
	1    950  6800
	-1   0    0    -1  
$EndComp
Text GLabel 1800 6400 0    50   Input ~ 0
VLED
Text GLabel 1800 6600 0    50   Input ~ 0
VBAT
Text GLabel 1800 6800 0    50   Input ~ 0
RST
Text GLabel 1800 6900 0    50   Input ~ 0
SI
Text GLabel 1800 7000 0    50   Input ~ 0
D\C
Text GLabel 1800 7100 0    50   Input ~ 0
CLK
Text GLabel 1800 7200 0    50   Input ~ 0
r6
$Comp
L power:GND #PWR013
U 1 1 6195DC18
P 1150 6400
F 0 "#PWR013" H 1150 6150 50  0001 C CNN
F 1 "GND" V 1155 6272 50  0000 R CNN
F 2 "" H 1150 6400 50  0001 C CNN
F 3 "" H 1150 6400 50  0001 C CNN
	1    1150 6400
	0    -1   -1   0   
$EndComp
Text GLabel 1150 6500 2    50   Input ~ 0
41
Text GLabel 1150 6600 2    50   Input ~ 0
42
Text GLabel 1150 6700 2    50   Input ~ 0
43
Text GLabel 1150 6800 2    50   Input ~ 0
44
Text GLabel 1150 6900 2    50   Input ~ 0
45
Text GLabel 1150 7000 2    50   Input ~ 0
46
Text GLabel 1150 7100 2    50   Input ~ 0
47
Text GLabel 1150 7200 2    50   Input ~ 0
48
$Comp
L 74xx:74HCT595 U6
U 1 1 61950BF7
P 1550 5700
F 0 "U6" V 1504 6344 50  0000 L CNN
F 1 "74HCT595" V 1600 5550 50  0000 L CNN
F 2 "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm" H 1550 5700 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf" H 1550 5700 50  0001 C CNN
	1    1550 5700
	0    1    1    0   
$EndComp
Text GLabel 8450 2450 3    50   Input ~ 0
9
Text GLabel 8350 2450 3    50   Input ~ 0
10
Text GLabel 8250 2450 3    50   Input ~ 0
11
Text GLabel 8150 2450 3    50   Input ~ 0
12
Text GLabel 8050 2450 3    50   Input ~ 0
13
Text GLabel 7950 2450 3    50   Input ~ 0
14
Text GLabel 7850 2450 3    50   Input ~ 0
15
Text GLabel 7750 2450 3    50   Input ~ 0
16
Text GLabel 6250 2450 3    50   Input ~ 0
17
Text GLabel 6150 2450 3    50   Input ~ 0
18
Text GLabel 6050 2450 3    50   Input ~ 0
19
Text GLabel 5950 2450 3    50   Input ~ 0
20
Text GLabel 5850 2450 3    50   Input ~ 0
21
Text GLabel 5750 2450 3    50   Input ~ 0
22
Text GLabel 5650 2450 3    50   Input ~ 0
23
Text GLabel 5550 2450 3    50   Input ~ 0
24
Text GLabel 6200 6100 3    50   Input ~ 0
25
Text GLabel 6100 6100 3    50   Input ~ 0
26
Text GLabel 6000 6100 3    50   Input ~ 0
27
Text GLabel 5900 6100 3    50   Input ~ 0
28
Text GLabel 5800 6100 3    50   Input ~ 0
29
Text GLabel 5700 6100 3    50   Input ~ 0
30
Text GLabel 5600 6100 3    50   Input ~ 0
31
Text GLabel 5500 6100 3    50   Input ~ 0
32
Text GLabel 4150 6100 3    50   Input ~ 0
33
Text GLabel 4050 6100 3    50   Input ~ 0
34
Text GLabel 3950 6100 3    50   Input ~ 0
35
Text GLabel 3850 6100 3    50   Input ~ 0
36
Text GLabel 3750 6100 3    50   Input ~ 0
37
Text GLabel 3650 6100 3    50   Input ~ 0
38
Text GLabel 3550 6100 3    50   Input ~ 0
39
Text GLabel 3450 6100 3    50   Input ~ 0
40
Text GLabel 1950 6100 3    50   Input ~ 0
41
Text GLabel 1850 6100 3    50   Input ~ 0
42
Text GLabel 1750 6100 3    50   Input ~ 0
43
Text GLabel 1650 6100 3    50   Input ~ 0
44
Text GLabel 1550 6100 3    50   Input ~ 0
45
Text GLabel 1450 6100 3    50   Input ~ 0
46
Text GLabel 1350 6100 3    50   Input ~ 0
47
Text GLabel 1250 6100 3    50   Input ~ 0
48
$Comp
L Connector_Generic:Conn_01x06 J14
U 1 1 61960EEE
P 8800 5150
F 0 "J14" H 8880 5142 50  0000 L CNN
F 1 "Conn_01x06" H 8880 5051 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical" H 8800 5150 50  0001 C CNN
F 3 "~" H 8800 5150 50  0001 C CNN
	1    8800 5150
	1    0    0    -1  
$EndComp
Text GLabel 8600 5050 0    50   Input ~ 0
SHIFTR_DATA
Text GLabel 8600 5350 0    50   Input ~ 0
SHIFTR_CLK
Text GLabel 8600 5250 0    50   Input ~ 0
SHIFTR_RST
Text GLabel 8600 5150 0    50   Input ~ 0
SHIFTR_LATCH_CLK
Text GLabel 8600 5650 0    50   Input ~ 0
SHIFTR_OUT
$Comp
L power:GND #PWR022
U 1 1 61963944
P 8600 5450
F 0 "#PWR022" H 8600 5200 50  0001 C CNN
F 1 "GND" V 8605 5322 50  0000 R CNN
F 2 "" H 8600 5450 50  0001 C CNN
F 3 "" H 8600 5450 50  0001 C CNN
	1    8600 5450
	0    1    1    0   
$EndComp
$Comp
L power:GND #PWR019
U 1 1 6196404E
P 9900 1650
F 0 "#PWR019" H 9900 1400 50  0001 C CNN
F 1 "GND" V 9905 1522 50  0000 R CNN
F 2 "" H 9900 1650 50  0001 C CNN
F 3 "" H 9900 1650 50  0001 C CNN
	1    9900 1650
	-1   0    0    1   
$EndComp
$Comp
L power:+3.3V #PWR021
U 1 1 619631DB
P 8600 4950
F 0 "#PWR021" H 8600 4800 50  0001 C CNN
F 1 "+3.3V" V 8615 5078 50  0000 L CNN
F 2 "" H 8600 4950 50  0001 C CNN
F 3 "" H 8600 4950 50  0001 C CNN
	1    8600 4950
	0    -1   -1   0   
$EndComp
$Comp
L Connector_Generic:Conn_01x01 J15
U 1 1 61967F35
P 8800 5650
F 0 "J15" H 8880 5692 50  0000 L CNN
F 1 "Conn_01x01" H 8880 5601 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical" H 8800 5650 50  0001 C CNN
F 3 "~" H 8800 5650 50  0001 C CNN
	1    8800 5650
	1    0    0    -1  
$EndComp
Text GLabel 10400 6100 0    50   Input ~ 0
VLED
Text GLabel 10000 4700 0    50   Input ~ 0
VBAT
Text GLabel 9850 5100 0    50   Input ~ 0
RST
Text GLabel 9850 5300 0    50   Input ~ 0
SI
Text GLabel 9850 5400 0    50   Input ~ 0
D\C
Text GLabel 9850 5200 0    50   Input ~ 0
CLK
Text GLabel 9950 4900 0    50   Input ~ 0
VDD_3V3
$Comp
L power:GND #PWR020
U 1 1 6196C1A4
P 10000 4600
F 0 "#PWR020" H 10000 4350 50  0001 C CNN
F 1 "GND" V 10005 4472 50  0000 R CNN
F 2 "" H 10000 4600 50  0001 C CNN
F 3 "" H 10000 4600 50  0001 C CNN
	1    10000 4600
	0    1    1    0   
$EndComp
Text GLabel 10400 2900 0    50   Input ~ 0
VDD_3V3
Text GLabel 8300 2850 0    50   Input ~ 0
VDD_3V3
Text GLabel 6100 2850 0    50   Input ~ 0
VDD_3V3
Text GLabel 6100 6500 0    50   Input ~ 0
VDD_3V3
Text GLabel 4050 6500 0    50   Input ~ 0
VDD_3V3
Text GLabel 1800 6500 0    50   Input ~ 0
VDD_3V3
$Comp
L Connector_Generic:Conn_01x02 J16
U 1 1 61970374
P 10600 6000
F 0 "J16" H 10680 6042 50  0000 L CNN
F 1 "Conn_01x02" H 10680 5951 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" H 10600 6000 50  0001 C CNN
F 3 "~" H 10600 6000 50  0001 C CNN
	1    10600 6000
	1    0    0    -1  
$EndComp
Wire Wire Line
	10400 4800 10400 4600
Wire Wire Line
	10000 4600 10400 4600
Wire Wire Line
	10400 4800 10450 4800
Wire Wire Line
	10450 4900 10350 4900
Wire Wire Line
	10350 4900 10350 4700
Wire Wire Line
	10000 4700 10350 4700
Wire Wire Line
	10300 5000 10450 5000
$Comp
L Device:R_Small R1
U 1 1 61976849
P 10250 5000
F 0 "R1" H 10309 5046 50  0000 L CNN
F 1 "1M" H 10309 4955 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 10250 5000 50  0001 C CNN
F 3 "~" H 10250 5000 50  0001 C CNN
	1    10250 5000
	1    0    0    -1  
$EndComp
Wire Wire Line
	9950 4900 10050 4900
Wire Wire Line
	10300 4900 10300 5000
Connection ~ 10250 4900
Wire Wire Line
	10250 4900 10300 4900
Wire Wire Line
	10150 5000 10150 4900
Connection ~ 10150 4900
Wire Wire Line
	10150 4900 10250 4900
Connection ~ 10050 4900
Wire Wire Line
	10050 4900 10150 4900
Wire Wire Line
	10450 5100 10250 5100
$Comp
L Connector_Generic:Conn_01x07 J13
U 1 1 6196D7D9
P 10650 5100
F 0 "J13" H 10730 5142 50  0000 L CNN
F 1 "Conn_01x07" H 10730 5051 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical" H 10650 5100 50  0001 C CNN
F 3 "~" H 10650 5100 50  0001 C CNN
	1    10650 5100
	1    0    0    -1  
$EndComp
Wire Wire Line
	9950 5150 9950 4900
Wire Wire Line
	9850 5400 9950 5400
Wire Wire Line
	9850 5300 10050 5300
Wire Wire Line
	9850 5100 10250 5100
Connection ~ 10250 5100
$Comp
L Device:R_Small R2
U 1 1 619841FB
P 10150 5100
F 0 "R2" H 10209 5146 50  0000 L CNN
F 1 "1M" H 10209 5055 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 10150 5100 50  0001 C CNN
F 3 "~" H 10150 5100 50  0001 C CNN
	1    10150 5100
	1    0    0    -1  
$EndComp
$Comp
L Device:R_Small R3
U 1 1 61984B06
P 10050 5150
F 0 "R3" H 10109 5196 50  0000 L CNN
F 1 "1M" H 10109 5105 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 10050 5150 50  0001 C CNN
F 3 "~" H 10050 5150 50  0001 C CNN
	1    10050 5150
	1    0    0    -1  
$EndComp
$Comp
L Device:R_Small R4
U 1 1 619854B4
P 9950 5250
F 0 "R4" H 10009 5296 50  0000 L CNN
F 1 "1M" H 10009 5205 50  0000 L CNN
F 2 "Resistor_SMD:R_0603_1608Metric" H 9950 5250 50  0001 C CNN
F 3 "~" H 9950 5250 50  0001 C CNN
	1    9950 5250
	1    0    0    -1  
$EndComp
Wire Wire Line
	9950 5350 9950 5400
Connection ~ 9950 5400
Wire Wire Line
	9950 5400 10450 5400
Wire Wire Line
	10050 5250 10050 5300
Connection ~ 10050 5300
Wire Wire Line
	10050 5300 10450 5300
Wire Wire Line
	10050 4900 10050 5050
Wire Wire Line
	10150 5200 10450 5200
Wire Wire Line
	10150 5200 9850 5200
Connection ~ 10150 5200
Wire Wire Line
	600  6100 1050 6100
Wire Wire Line
	5350 2450 4650 2450
Wire Wire Line
	4650 2450 4650 4300
Wire Wire Line
	4650 4300 6200 4300
Wire Wire Line
	6200 4300 6200 5300
$Comp
L Connector_Generic:Conn_01x02 J21
U 1 1 6194B5D8
P 10600 3800
F 0 "J21" H 10680 3842 50  0000 L CNN
F 1 "Conn_01x02" H 10680 3751 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" H 10600 3800 50  0001 C CNN
F 3 "~" H 10600 3800 50  0001 C CNN
	1    10600 3800
	1    0    0    -1  
$EndComp
Wire Wire Line
	10400 3800 10100 3800
Wire Wire Line
	10100 3800 10100 3100
Wire Wire Line
	10100 3100 10400 3100
Text GLabel 8300 3750 3    50   Input ~ 0
LedIn2
$Comp
L Connector_Generic:Conn_01x02 J22
U 1 1 6194D982
P 8500 3750
F 0 "J22" H 8580 3792 50  0000 L CNN
F 1 "Conn_01x02" H 8580 3701 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" H 8500 3750 50  0001 C CNN
F 3 "~" H 8500 3750 50  0001 C CNN
	1    8500 3750
	1    0    0    -1  
$EndComp
Wire Wire Line
	8300 3750 8000 3750
Wire Wire Line
	8000 3750 8000 3050
Text GLabel 6100 3750 3    50   Input ~ 0
LedIn3
$Comp
L Connector_Generic:Conn_01x02 J23
U 1 1 6194E724
P 6300 3750
F 0 "J23" H 6380 3792 50  0000 L CNN
F 1 "Conn_01x02" H 6380 3701 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" H 6300 3750 50  0001 C CNN
F 3 "~" H 6300 3750 50  0001 C CNN
	1    6300 3750
	1    0    0    -1  
$EndComp
Wire Wire Line
	6100 3750 5800 3750
Wire Wire Line
	5800 3750 5800 3050
Text GLabel 6100 7400 3    50   Input ~ 0
LedIn4
$Comp
L Connector_Generic:Conn_01x02 J24
U 1 1 6194F6BF
P 6300 7400
F 0 "J24" H 6380 7442 50  0000 L CNN
F 1 "Conn_01x02" H 6380 7351 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" H 6300 7400 50  0001 C CNN
F 3 "~" H 6300 7400 50  0001 C CNN
	1    6300 7400
	1    0    0    -1  
$EndComp
Wire Wire Line
	6100 7400 5800 7400
Wire Wire Line
	5800 7400 5800 6700
Text GLabel 4050 7400 3    50   Input ~ 0
LedIn5
$Comp
L Connector_Generic:Conn_01x02 J25
U 1 1 619506C9
P 4250 7400
F 0 "J25" H 4330 7442 50  0000 L CNN
F 1 "Conn_01x02" H 4330 7351 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" H 4250 7400 50  0001 C CNN
F 3 "~" H 4250 7400 50  0001 C CNN
	1    4250 7400
	1    0    0    -1  
$EndComp
Wire Wire Line
	4050 7400 3750 7400
Wire Wire Line
	3750 7400 3750 6700
Text GLabel 1800 7400 3    50   Input ~ 0
LedIn6
$Comp
L Connector_Generic:Conn_01x02 J26
U 1 1 619518C5
P 2000 7400
F 0 "J26" H 2080 7442 50  0000 L CNN
F 1 "Conn_01x02" H 2080 7351 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" H 2000 7400 50  0001 C CNN
F 3 "~" H 2000 7400 50  0001 C CNN
	1    2000 7400
	1    0    0    -1  
$EndComp
Wire Wire Line
	1800 7400 1500 7400
Wire Wire Line
	1500 7400 1500 6700
Wire Wire Line
	8000 3050 8300 3050
Wire Wire Line
	5800 3050 6100 3050
Wire Wire Line
	3750 6700 4050 6700
Wire Wire Line
	1500 6700 1800 6700
Wire Wire Line
	5800 6700 6100 6700
$Comp
L power:GND #PWR026
U 1 1 6195E026
P 1350 5300
F 0 "#PWR026" H 1350 5050 50  0001 C CNN
F 1 "GND" V 1355 5172 50  0000 R CNN
F 2 "" H 1350 5300 50  0001 C CNN
F 3 "" H 1350 5300 50  0001 C CNN
	1    1350 5300
	-1   0    0    1   
$EndComp
$Comp
L power:GND #PWR027
U 1 1 6195F57D
P 3550 5300
F 0 "#PWR027" H 3550 5050 50  0001 C CNN
F 1 "GND" V 3555 5172 50  0000 R CNN
F 2 "" H 3550 5300 50  0001 C CNN
F 3 "" H 3550 5300 50  0001 C CNN
	1    3550 5300
	-1   0    0    1   
$EndComp
$Comp
L power:GND #PWR028
U 1 1 61960AA2
P 5600 5300
F 0 "#PWR028" H 5600 5050 50  0001 C CNN
F 1 "GND" V 5605 5172 50  0000 R CNN
F 2 "" H 5600 5300 50  0001 C CNN
F 3 "" H 5600 5300 50  0001 C CNN
	1    5600 5300
	-1   0    0    1   
$EndComp
$Comp
L power:GND #PWR024
U 1 1 61961F70
P 5650 1650
F 0 "#PWR024" H 5650 1400 50  0001 C CNN
F 1 "GND" V 5655 1522 50  0000 R CNN
F 2 "" H 5650 1650 50  0001 C CNN
F 3 "" H 5650 1650 50  0001 C CNN
	1    5650 1650
	-1   0    0    1   
$EndComp
$Comp
L power:GND #PWR025
U 1 1 6196344B
P 7850 1650
F 0 "#PWR025" H 7850 1400 50  0001 C CNN
F 1 "GND" V 7855 1522 50  0000 R CNN
F 2 "" H 7850 1650 50  0001 C CNN
F 3 "" H 7850 1650 50  0001 C CNN
	1    7850 1650
	-1   0    0    1   
$EndComp
Wire Wire Line
	10400 3900 10250 3900
Wire Wire Line
	10250 3900 10250 3600
Wire Wire Line
	10250 3600 10400 3600
Wire Wire Line
	8300 3850 8100 3850
Wire Wire Line
	8100 3850 8100 3550
Wire Wire Line
	8100 3550 8300 3550
Wire Wire Line
	6100 3850 5900 3850
Wire Wire Line
	5900 3850 5900 3550
Wire Wire Line
	5900 3550 6100 3550
Wire Wire Line
	6100 7500 5900 7500
Wire Wire Line
	5900 7500 5900 7200
Wire Wire Line
	5900 7200 6100 7200
Wire Wire Line
	4050 7500 3900 7500
Wire Wire Line
	3900 7500 3900 7200
Wire Wire Line
	3900 7200 4050 7200
Wire Wire Line
	1800 7500 1600 7500
Wire Wire Line
	1600 7500 1600 7200
Wire Wire Line
	1600 7200 1800 7200
Text GLabel 2700 5300 1    50   Input ~ 0
SHIFTR_AOUT
Text GLabel 8600 6050 0    50   Input ~ 0
SHIFTR_AOUT
$Comp
L Connector_Generic:Conn_01x01 J17
U 1 1 619D0096
P 8800 6050
F 0 "J17" H 8880 6092 50  0000 L CNN
F 1 "Conn_01x01" H 8880 6001 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical" H 8800 6050 50  0001 C CNN
F 3 "~" H 8800 6050 50  0001 C CNN
	1    8800 6050
	1    0    0    -1  
$EndComp
$Comp
L power:GND #PWR023
U 1 1 6196CC7C
P 10400 6000
F 0 "#PWR023" H 10400 5750 50  0001 C CNN
F 1 "GND" V 10405 5872 50  0000 R CNN
F 2 "" H 10400 6000 50  0001 C CNN
F 3 "" H 10400 6000 50  0001 C CNN
	1    10400 6000
	0    1    1    0   
$EndComp
$EndSCHEMATC
