#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "gb.h"
static void icdpix(GB_gameboy_t*gb, uint8_t c){}
static void hres(GB_gameboy_t*gb){}
static void vres(GB_gameboy_t*gb){}
static void joyp(GB_gameboy_t*gb, uint8_t v){}
static uint32_t rgb(GB_gameboy_t*gb,uint8_t r,uint8_t g,uint8_t b){return 0;}
static uint32_t px[256*224];
static void samp(GB_gameboy_t*gb, GB_sample_t*s){}
static void vbl(GB_gameboy_t*gb){}
static uint8_t rdm(GB_gameboy_t*gb,uint16_t a,uint8_t d){return d;}
int main(int argc,char**argv){
  // boottime bootrom rom [model 1=sgb 2=sgb2] -> prints 8MHz units and M-cycles until PC=$0100
  FILE*f=fopen(argv[1],"rb"); unsigned char boot[256]; fread(boot,1,256,f); fclose(f);
  f=fopen(argv[2],"rb"); fseek(f,0,SEEK_END); long n=ftell(f); fseek(f,0,SEEK_SET); unsigned char*rom=malloc(n); fread(rom,1,n,f); fclose(f);
  int model = argc>3 && atoi(argv[3])==2 ? GB_MODEL_SGB2_NO_SFC : GB_MODEL_SGB_NO_SFC;
  static GB_gameboy_t gb; GB_init(&gb, model);
  GB_set_pixels_output(&gb,px); GB_set_rgb_encode_callback(&gb,rgb);
  GB_set_icd_pixel_callback(&gb,icdpix); GB_set_icd_hreset_callback(&gb,hres); GB_set_icd_vreset_callback(&gb,vres);
  GB_set_joyp_write_callback(&gb,joyp); GB_set_sample_rate_by_clocks(&gb,256); GB_apu_set_sample_callback(&gb,samp); GB_set_vblank_callback(&gb,vbl); GB_set_read_memory_callback(&gb,rdm);
  GB_load_boot_rom_from_buffer(&gb,boot,256); GB_load_rom_from_buffer(&gb,rom,n);
  GB_reset(&gb);
  unsigned long long t=0;
  while(1){ if(gb.pc==0x100 && gb.boot_rom_finished) break; t+=GB_run(&gb); if(t>800000000ULL){printf("timeout\n");return 1;} }
  printf("%llu %llu\n", t, t/8);
  return 0;
}
