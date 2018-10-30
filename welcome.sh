#!/bin/sh
clear;
echo ""
echo "================================================================================"
echo ""
echo " Intermediate Filament Tracking Software - Version 1.0 (GNU GPL v3.0)"
echo " (c) 2018 Software Competence Center GmbH. All Rights Reserved."
echo ""
echo " More information: https://github.com/SCCH-KVS/IFTracking"
echo ""
echo "================================================================================"
echo ""

options=("Process image sequence" "Detect filaments" "Track filaments" "Overlay filaments over the sequence" "Perform all routines" "Exit")

PS3="Please, enter the operation index: "

while true; do
	echo "The following operations are available:"
	select opt in "${options[@]}"; do
		case $REPLY in
			1) sh Step_1.sh; break;;
			2) sh Step_2.sh; break;;
			3) sh Step_3.sh; break;;
			4) sh Step_4.sh; break;;
			5) sh run_all.sh; break;;
			6) break 2;;
		esac
	done
done 

echo ""