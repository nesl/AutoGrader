#! /bin/bash

cd Wire
quartus_map --read_settings_files=on --write_settings_files=off Wire -c Wire
quartus_fit --read_settings_files=on --write_settings_files=off Wire -c Wire
quartus_asm --read_settings_files=on --write_settings_files=off Wire -c Wire
quartus_sta Wire -c Wire
quartus_eda --read_settings_files=on --write_settings_files=off Wire -c Wire
quartus_pgm -c USB-Blaster output_files/Wire.cdf
cd ..