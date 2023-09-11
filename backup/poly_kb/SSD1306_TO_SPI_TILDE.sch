EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 2 5
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
Wire Wire Line
	2450 2150 1750 2150
Wire Wire Line
	2450 2050 1750 2050
Text HLabel 1750 2450 0    50   Input ~ 0
SDIN
Text HLabel 1750 2350 0    50   Input ~ 0
SCLK
Text HLabel 1750 2250 0    50   Input ~ 0
D-C
Text HLabel 1750 2050 0    50   Input ~ 0
CS
Text HLabel 1750 2150 0    50   Input ~ 0
RESET
Text Label 2200 2450 0    50   ~ 0
SDIN
Text Label 2200 2350 0    50   ~ 0
SCLK
Text Label 2200 2250 0    50   ~ 0
D-C
Text Label 2200 2050 0    50   ~ 0
CS
Text Label 2200 2150 0    50   ~ 0
Reset
Connection ~ 2200 2850
$Comp
L power:GND #PWR0101
U 1 1 5FC4B754
P 2200 2850
AR Path="/5FC0795D/5FC4B754" Ref="#PWR0101"  Part="1" 
AR Path="/5FC10791/5FC4B754" Ref="#PWR0110"  Part="1" 
AR Path="/5FC10877/5FC4B754" Ref="#PWR0119"  Part="1" 
AR Path="/5FC10951/5FC4B754" Ref="#PWR0128"  Part="1" 
F 0 "#PWR0101" H 2200 2600 50  0001 C CNN
F 1 "GND" H 2205 2677 50  0000 C CNN
F 2 "" H 2200 2850 50  0001 C CNN
F 3 "" H 2200 2850 50  0001 C CNN
	1    2200 2850
	1    0    0    -1  
$EndComp
Wire Wire Line
	1900 2850 2200 2850
Wire Wire Line
	2200 2650 1900 2650
Connection ~ 2200 2650
Wire Wire Line
	1900 2650 1500 2650
Connection ~ 1900 2650
Wire Wire Line
	2450 2650 2200 2650
$Comp
L Device:C_Small C2
U 1 1 5FC4B760
P 1900 2750
AR Path="/5FC0795D/5FC4B760" Ref="C2"  Part="1" 
AR Path="/5FC10791/5FC4B760" Ref="C8"  Part="1" 
AR Path="/5FC10877/5FC4B760" Ref="C14"  Part="1" 
AR Path="/5FC10951/5FC4B760" Ref="C20"  Part="1" 
F 0 "C2" H 1808 2704 50  0000 R CNN
F 1 "4.7uF" H 1808 2795 50  0000 R CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 1900 2750 50  0001 C CNN
F 3 "~" H 1900 2750 50  0001 C CNN
	1    1900 2750
	-1   0    0    1   
$EndComp
$Comp
L Device:C_Small C5
U 1 1 5FC4B766
P 2200 2750
AR Path="/5FC0795D/5FC4B766" Ref="C5"  Part="1" 
AR Path="/5FC10791/5FC4B766" Ref="C11"  Part="1" 
AR Path="/5FC10877/5FC4B766" Ref="C17"  Part="1" 
AR Path="/5FC10951/5FC4B766" Ref="C23"  Part="1" 
F 0 "C5" H 2108 2704 50  0000 R CNN
F 1 "100nF" H 2108 2795 50  0000 R CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 2200 2750 50  0001 C CNN
F 3 "~" H 2200 2750 50  0001 C CNN
	1    2200 2750
	-1   0    0    1   
$EndComp
Wire Wire Line
	2450 2550 2100 2550
$Comp
L power:GND #PWR0102
U 1 1 5FC4B76D
P 1900 2550
AR Path="/5FC0795D/5FC4B76D" Ref="#PWR0102"  Part="1" 
AR Path="/5FC10791/5FC4B76D" Ref="#PWR0111"  Part="1" 
AR Path="/5FC10877/5FC4B76D" Ref="#PWR0120"  Part="1" 
AR Path="/5FC10951/5FC4B76D" Ref="#PWR0129"  Part="1" 
F 0 "#PWR0102" H 1900 2300 50  0001 C CNN
F 1 "GND" V 1905 2422 50  0000 R CNN
F 2 "" H 1900 2550 50  0001 C CNN
F 3 "" H 1900 2550 50  0001 C CNN
	1    1900 2550
	0    1    1    0   
$EndComp
$Comp
L Device:C_Small C3
U 1 1 5FC4B773
P 2000 2550
AR Path="/5FC0795D/5FC4B773" Ref="C3"  Part="1" 
AR Path="/5FC10791/5FC4B773" Ref="C9"  Part="1" 
AR Path="/5FC10877/5FC4B773" Ref="C15"  Part="1" 
AR Path="/5FC10951/5FC4B773" Ref="C21"  Part="1" 
F 0 "C3" V 1771 2550 50  0000 C CNN
F 1 "2.2uF" V 1862 2550 50  0000 C CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 2000 2550 50  0001 C CNN
F 3 "~" H 2000 2550 50  0001 C CNN
	1    2000 2550
	0    1    1    0   
$EndComp
$Comp
L power:GND #PWR0103
U 1 1 5FC4B779
P 1800 1850
AR Path="/5FC0795D/5FC4B779" Ref="#PWR0103"  Part="1" 
AR Path="/5FC10791/5FC4B779" Ref="#PWR0112"  Part="1" 
AR Path="/5FC10877/5FC4B779" Ref="#PWR0121"  Part="1" 
AR Path="/5FC10951/5FC4B779" Ref="#PWR0130"  Part="1" 
F 0 "#PWR0103" H 1800 1600 50  0001 C CNN
F 1 "GND" V 1805 1722 50  0000 R CNN
F 2 "" H 1800 1850 50  0001 C CNN
F 3 "" H 1800 1850 50  0001 C CNN
	1    1800 1850
	0    1    1    0   
$EndComp
Connection ~ 2450 1850
Wire Wire Line
	2450 1850 2000 1850
Connection ~ 2450 1950
Wire Wire Line
	2450 1850 2450 1950
$Comp
L Device:C_Small C1
U 1 1 5FC4B783
P 1900 1850
AR Path="/5FC0795D/5FC4B783" Ref="C1"  Part="1" 
AR Path="/5FC10791/5FC4B783" Ref="C7"  Part="1" 
AR Path="/5FC10877/5FC4B783" Ref="C13"  Part="1" 
AR Path="/5FC10951/5FC4B783" Ref="C19"  Part="1" 
F 0 "C1" V 1671 1850 50  0000 C CNN
F 1 "2.2uF" V 1762 1850 50  0000 C CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 1900 1850 50  0001 C CNN
F 3 "~" H 1900 1850 50  0001 C CNN
	1    1900 1850
	0    1    1    0   
$EndComp
$Comp
L power:+3.3V #PWR0104
U 1 1 5FC4B789
P 1500 2650
AR Path="/5FC0795D/5FC4B789" Ref="#PWR0104"  Part="1" 
AR Path="/5FC10791/5FC4B789" Ref="#PWR0113"  Part="1" 
AR Path="/5FC10877/5FC4B789" Ref="#PWR0122"  Part="1" 
AR Path="/5FC10951/5FC4B789" Ref="#PWR0131"  Part="1" 
F 0 "#PWR0104" H 1500 2500 50  0001 C CNN
F 1 "+3.3V" V 1515 2778 50  0000 L CNN
F 2 "" H 1500 2650 50  0001 C CNN
F 3 "" H 1500 2650 50  0001 C CNN
	1    1500 2650
	0    -1   -1   0   
$EndComp
$Comp
L power:+3.3V #PWR0105
U 1 1 5FC4B78F
P 2450 1950
AR Path="/5FC0795D/5FC4B78F" Ref="#PWR0105"  Part="1" 
AR Path="/5FC10791/5FC4B78F" Ref="#PWR0114"  Part="1" 
AR Path="/5FC10877/5FC4B78F" Ref="#PWR0123"  Part="1" 
AR Path="/5FC10951/5FC4B78F" Ref="#PWR0132"  Part="1" 
F 0 "#PWR0105" H 2450 1800 50  0001 C CNN
F 1 "+3.3V" V 2465 2078 50  0000 L CNN
F 2 "" H 2450 1950 50  0001 C CNN
F 3 "" H 2450 1950 50  0001 C CNN
	1    2450 1950
	0    -1   -1   0   
$EndComp
Wire Wire Line
	2150 1750 2450 1750
Wire Wire Line
	2150 1650 2150 1750
Wire Wire Line
	2450 1650 2350 1650
Wire Wire Line
	2000 1550 2450 1550
Wire Wire Line
	2000 1450 2000 1550
Wire Wire Line
	2450 1450 2200 1450
$Comp
L Device:C_Small C6
U 1 1 5FC4B79B
P 2250 1650
AR Path="/5FC0795D/5FC4B79B" Ref="C6"  Part="1" 
AR Path="/5FC10791/5FC4B79B" Ref="C12"  Part="1" 
AR Path="/5FC10877/5FC4B79B" Ref="C18"  Part="1" 
AR Path="/5FC10951/5FC4B79B" Ref="C24"  Part="1" 
F 0 "C6" V 2021 1650 50  0000 C CNN
F 1 "1uF" V 2112 1650 50  0000 C CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 2250 1650 50  0001 C CNN
F 3 "~" H 2250 1650 50  0001 C CNN
	1    2250 1650
	0    1    1    0   
$EndComp
$Comp
L Device:C_Small C4
U 1 1 5FC4B7A1
P 2100 1450
AR Path="/5FC0795D/5FC4B7A1" Ref="C4"  Part="1" 
AR Path="/5FC10791/5FC4B7A1" Ref="C10"  Part="1" 
AR Path="/5FC10877/5FC4B7A1" Ref="C16"  Part="1" 
AR Path="/5FC10951/5FC4B7A1" Ref="C22"  Part="1" 
F 0 "C4" V 1871 1450 50  0000 C CNN
F 1 "1uF" V 1962 1450 50  0000 C CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 2100 1450 50  0001 C CNN
F 3 "~" H 2100 1450 50  0001 C CNN
	1    2100 1450
	0    1    1    0   
$EndComp
$Comp
L power:GND #PWR0106
U 1 1 5FC4B7A7
P 2450 1350
AR Path="/5FC0795D/5FC4B7A7" Ref="#PWR0106"  Part="1" 
AR Path="/5FC10791/5FC4B7A7" Ref="#PWR0115"  Part="1" 
AR Path="/5FC10877/5FC4B7A7" Ref="#PWR0124"  Part="1" 
AR Path="/5FC10951/5FC4B7A7" Ref="#PWR0133"  Part="1" 
F 0 "#PWR0106" H 2450 1100 50  0001 C CNN
F 1 "GND" V 2455 1222 50  0000 R CNN
F 2 "" H 2450 1350 50  0001 C CNN
F 3 "" H 2450 1350 50  0001 C CNN
	1    2450 1350
	0    1    1    0   
$EndComp
$Comp
L Connector_Generic:Conn_01x16 J1
U 1 1 5FC4B7AD
P 2650 1850
AR Path="/5FC0795D/5FC4B7AD" Ref="J1"  Part="1" 
AR Path="/5FC10791/5FC4B7AD" Ref="J2"  Part="1" 
AR Path="/5FC10877/5FC4B7AD" Ref="J3"  Part="1" 
AR Path="/5FC10951/5FC4B7AD" Ref="J4"  Part="1" 
F 0 "J1" H 2730 1842 50  0000 L CNN
F 1 "Conn_01x16" H 2730 1751 50  0000 L CNN
F 2 "poly_kb:FPC_16_AFC11-S16ICA-00" H 2650 1850 50  0001 C CNN
F 3 "https://datasheet.lcsc.com/szlcsc/1811021329_JUSHUO-AFC11-S16ICA-00_C262501.pdf" H 2650 1850 50  0001 C CNN
	1    2650 1850
	1    0    0    -1  
$EndComp
$Comp
L power:GND #PWR0107
U 1 1 5FC4B7B3
P 2450 1150
AR Path="/5FC0795D/5FC4B7B3" Ref="#PWR0107"  Part="1" 
AR Path="/5FC10791/5FC4B7B3" Ref="#PWR0116"  Part="1" 
AR Path="/5FC10877/5FC4B7B3" Ref="#PWR0125"  Part="1" 
AR Path="/5FC10951/5FC4B7B3" Ref="#PWR0134"  Part="1" 
F 0 "#PWR0107" H 2450 900 50  0001 C CNN
F 1 "GND" V 2455 1022 50  0000 R CNN
F 2 "" H 2450 1150 50  0001 C CNN
F 3 "" H 2450 1150 50  0001 C CNN
	1    2450 1150
	0    1    1    0   
$EndComp
Wire Wire Line
	2450 2250 1750 2250
Wire Wire Line
	2450 2350 1750 2350
Wire Wire Line
	2450 2450 1750 2450
Text Label 2400 1250 0    50   ~ 0
NC
$Comp
L LED:WS2812B D1
U 1 1 5FC0D39F
P 3650 1950
AR Path="/5FC0795D/5FC0D39F" Ref="D1"  Part="1" 
AR Path="/5FC10791/5FC0D39F" Ref="D2"  Part="1" 
AR Path="/5FC10877/5FC0D39F" Ref="D3"  Part="1" 
AR Path="/5FC10951/5FC0D39F" Ref="D4"  Part="1" 
F 0 "D1" H 3994 1996 50  0000 L CNN
F 1 "WS2812B" H 3994 1905 50  0000 L CNN
F 2 "LED_SMD:LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm" H 3700 1650 50  0001 L TNN
F 3 "https://cdn-shop.adafruit.com/datasheets/WS2812B.pdf" H 3750 1575 50  0001 L TNN
	1    3650 1950
	1    0    0    -1  
$EndComp
$Comp
L power:GND #PWR0108
U 1 1 5FC0EC25
P 3650 2250
AR Path="/5FC0795D/5FC0EC25" Ref="#PWR0108"  Part="1" 
AR Path="/5FC10791/5FC0EC25" Ref="#PWR0117"  Part="1" 
AR Path="/5FC10877/5FC0EC25" Ref="#PWR0126"  Part="1" 
AR Path="/5FC10951/5FC0EC25" Ref="#PWR0135"  Part="1" 
F 0 "#PWR0108" H 3650 2000 50  0001 C CNN
F 1 "GND" H 3655 2077 50  0000 C CNN
F 2 "" H 3650 2250 50  0001 C CNN
F 3 "" H 3650 2250 50  0001 C CNN
	1    3650 2250
	1    0    0    -1  
$EndComp
$Comp
L power:+5V #PWR0109
U 1 1 5FC0F99E
P 3650 1650
AR Path="/5FC0795D/5FC0F99E" Ref="#PWR0109"  Part="1" 
AR Path="/5FC10791/5FC0F99E" Ref="#PWR0118"  Part="1" 
AR Path="/5FC10877/5FC0F99E" Ref="#PWR0127"  Part="1" 
AR Path="/5FC10951/5FC0F99E" Ref="#PWR0136"  Part="1" 
F 0 "#PWR0109" H 3650 1500 50  0001 C CNN
F 1 "+5V" H 3665 1823 50  0000 C CNN
F 2 "" H 3650 1650 50  0001 C CNN
F 3 "" H 3650 1650 50  0001 C CNN
	1    3650 1650
	1    0    0    -1  
$EndComp
Text HLabel 3350 1950 0    50   Input ~ 0
LED_DIN
Text HLabel 3950 1950 2    50   Input ~ 0
LED_DOUT
$EndSCHEMATC