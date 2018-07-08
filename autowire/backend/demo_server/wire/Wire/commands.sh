#! /bin/bash

quartus_map --read_settings_files=on --write_settings_files=off Wire -c Wire
quartus_fit --read_settings_files=on --write_settings_files=off Wire -c Wire
quartus_asm --read_settings_files=on --write_settings_files=off Wire -c Wire
quartus_sta Wire -c Wire
quartus_eda --read_settings_files=on --write_settings_files=off Wire -c Wire
quartus_pgm -c USB-Blaster -m JTAG -o p\;output_files/Wire.sof

