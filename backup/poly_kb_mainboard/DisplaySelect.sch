EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 11 11
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
L 74xx:74HCT595 U?
U 1 1 60528FA6
P 6250 3700
F 0 "U?" V 6000 2950 50  0000 L CNN
F 1 "74HCT595" V 5850 2950 50  0000 L CNN
F 2 "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm" H 6250 3700 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf" H 6250 3700 50  0001 C CNN
F 4 "C6767" V 6500 2800 50  0000 L BNN "LCSC"
	1    6250 3700
	0    1    1    0   
$EndComp
$Comp
L power:GND #PWR?
U 1 1 60528FAC
P 5550 3700
F 0 "#PWR?" H 5550 3450 50  0001 C CNN
F 1 "GND" V 5555 3572 50  0000 R CNN
F 2 "" H 5550 3700 50  0001 C CNN
F 3 "" H 5550 3700 50  0001 C CNN
	1    5550 3700
	0    1    1    0   
$EndComp
$Comp
L power:+3.3V #PWR?
U 1 1 60528FB2
P 6850 3700
F 0 "#PWR?" H 6850 3550 50  0001 C CNN
F 1 "+3.3V" V 7000 3700 50  0000 L CNN
F 2 "" H 6850 3700 50  0001 C CNN
F 3 "" H 6850 3700 50  0001 C CNN
	1    6850 3700
	0    1    1    0   
$EndComp
Text GLabel 5400 2950 0    50   Input ~ 0
SPI1_SS
Text GLabel 6850 3150 2    50   Input ~ 0
SHIFTR_DATA
Wire Wire Line
	6850 3150 6650 3150
Wire Wire Line
	6650 3150 6650 3300
Text GLabel 6850 3050 2    50   Input ~ 0
SHIFTR_CLK
Wire Wire Line
	6850 3050 6600 3050
Text GLabel 6150 3050 1    50   Input ~ 0
SHIFTR_LATCH_CLK
Wire Wire Line
	6150 3050 6150 3300
$Comp
L power:+3.3V #PWR?
U 1 1 60528FC0
P 5950 2950
F 0 "#PWR?" H 5950 2800 50  0001 C CNN
F 1 "+3.3V" H 5900 3100 50  0000 C CNN
F 2 "" H 5950 2950 50  0001 C CNN
F 3 "" H 5950 2950 50  0001 C CNN
	1    5950 2950
	-1   0    0    1   
$EndComp
$Comp
L power:+3.3V #PWR?
U 1 1 60528FC6
P 6350 2950
F 0 "#PWR?" H 6350 2800 50  0001 C CNN
F 1 "+3.3V" H 6365 3123 50  0000 C CNN
F 2 "" H 6350 2950 50  0001 C CNN
F 3 "" H 6350 2950 50  0001 C CNN
	1    6350 2950
	-1   0    0    1   
$EndComp
$Comp
L Connector_Generic:Conn_01x03 J?
U 1 1 60528FCC
P 6450 2750
F 0 "J?" V 6550 2500 50  0000 C CNN
F 1 "/MR" V 6550 2750 50  0000 C CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical" H 6450 2750 50  0001 C CNN
F 3 "~" H 6450 2750 50  0001 C CNN
	1    6450 2750
	0    -1   -1   0   
$EndComp
Wire Wire Line
	6450 3250 6600 3250
Wire Wire Line
	6600 3250 6600 3050
Wire Wire Line
	6450 3250 6450 3300
Text GLabel 6850 2950 2    50   Input ~ 0
SHIFTR_NMASTER_RST
Text GLabel 6150 4100 3    50   Input ~ 0
K_6
Text GLabel 6250 4100 3    50   Input ~ 0
K_5
Text GLabel 6350 4100 3    50   Input ~ 0
K_4
Text GLabel 6650 4100 3    50   Input ~ 0
K_1
Text GLabel 6550 4100 3    50   Input ~ 0
K_2
Text GLabel 6450 4100 3    50   Input ~ 0
K_3
Text Notes 4750 2050 0    50   ~ 0
Display CS Selection
$Comp
L Connector_Generic:Conn_01x03 J?
U 1 1 60528FDD
P 5850 2750
F 0 "J?" V 5950 3000 50  0000 C CNN
F 1 "/OE" V 5950 2750 50  0000 C CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical" H 5850 2750 50  0001 C CNN
F 3 "~" H 5850 2750 50  0001 C CNN
	1    5850 2750
	0    1    -1   0   
$EndComp
Wire Wire Line
	6550 2950 6850 2950
Wire Wire Line
	6350 3300 6350 3200
Wire Wire Line
	6350 3150 6450 3150
Wire Wire Line
	6450 3150 6450 2950
Wire Wire Line
	6050 3300 6050 3150
Wire Wire Line
	6050 3150 5850 3150
Wire Wire Line
	5850 3150 5850 2950
Wire Wire Line
	5750 2950 5400 2950
$Comp
L 74xx:74HCT595 U?
U 1 1 60528FEC
P 4350 3700
F 0 "U?" V 4100 2950 50  0000 L CNN
F 1 "74HCT595" V 3950 2950 50  0000 L CNN
F 2 "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm" H 4350 3700 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf" H 4350 3700 50  0001 C CNN
F 4 "C6767" V 4600 2800 50  0000 L BNN "LCSC"
	1    4350 3700
	0    1    1    0   
$EndComp
$Comp
L power:GND #PWR?
U 1 1 60528FF2
P 3650 3700
F 0 "#PWR?" H 3650 3450 50  0001 C CNN
F 1 "GND" V 3655 3572 50  0000 R CNN
F 2 "" H 3650 3700 50  0001 C CNN
F 3 "" H 3650 3700 50  0001 C CNN
	1    3650 3700
	0    1    1    0   
$EndComp
$Comp
L power:+3.3V #PWR?
U 1 1 60528FF8
P 4950 3700
F 0 "#PWR?" H 4950 3550 50  0001 C CNN
F 1 "+3.3V" V 5100 3700 50  0000 L CNN
F 2 "" H 4950 3700 50  0001 C CNN
F 3 "" H 4950 3700 50  0001 C CNN
	1    4950 3700
	0    1    1    0   
$EndComp
Text GLabel 6050 4100 3    50   Input ~ 0
K_7
Text GLabel 5950 4100 3    50   Input ~ 0
K_8
Text GLabel 4750 4100 3    50   Input ~ 0
K_9
Wire Wire Line
	4150 4350 4150 4100
Wire Wire Line
	4050 4100 4050 4350
Wire Wire Line
	3950 4350 3950 4100
Wire Wire Line
	3950 4100 3850 4100
Wire Wire Line
	5850 3150 4150 3150
Wire Wire Line
	4150 3150 4150 3300
Connection ~ 5850 3150
Wire Wire Line
	6350 3200 4450 3200
Wire Wire Line
	4450 3200 4450 3300
Connection ~ 6350 3200
Wire Wire Line
	6350 3200 6350 3150
Text GLabel 4250 3050 1    50   Input ~ 0
SHIFTR_LATCH_CLK
Wire Wire Line
	4250 3050 4250 3300
Wire Wire Line
	6450 3250 4550 3250
Wire Wire Line
	4550 3250 4550 3300
Connection ~ 6450 3250
Wire Wire Line
	5750 4100 5200 4100
Wire Wire Line
	5200 4100 5200 3300
Wire Wire Line
	5200 3300 4750 3300
$Comp
L Connector_Generic:Conn_01x08 J?
U 1 1 60529014
P 4350 4550
F 0 "J?" V 4222 4930 50  0000 L CNN
F 1 "SHIFTR_K10-K16+C" V 4450 4350 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical" H 4350 4550 50  0001 C CNN
F 3 "~" H 4350 4550 50  0001 C CNN
	1    4350 4550
	0    1    1    0   
$EndComp
Wire Wire Line
	4250 4100 4250 4350
Wire Wire Line
	4350 4100 4350 4350
Wire Wire Line
	4450 4100 4450 4350
Wire Wire Line
	4550 4100 4550 4350
Wire Wire Line
	4650 4100 4650 4350
$EndSCHEMATC
