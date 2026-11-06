#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include "libretro.h"
static const char *sysdir; static const char *bios; static int pixfmt=0; static unsigned g_fr=0;
static void logcb(enum retro_log_level l,const char*fmt,...){va_list a;va_start(a,fmt);vfprintf(stderr,fmt,a);va_end(a);}
static bool env(unsigned cmd,void*data){
  switch(cmd){
  case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY: *(const char**)data=sysdir; return true;
  case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY: *(const char**)data=sysdir; return true;
  case RETRO_ENVIRONMENT_GET_VARIABLE: { struct retro_variable*v=data;
     if(!strcmp(v->key,"bsnes_sgb_bios")){v->value=bios;return true;}
     if(!strcmp(v->key,"bsnes_entropy")){v->value="None";return true;}
     if(!strcmp(v->key,"bsnes_ppu_fast")){v->value="OFF";return true;}
     v->value=NULL; return false; }
  case RETRO_ENVIRONMENT_GET_LOG_INTERFACE: ((struct retro_log_callback*)data)->log=logcb; return true;
  case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: pixfmt=*(int*)data; return true;
  default: return false;}
}

static void vid(const void*d,unsigned w,unsigned h,size_t p){
  if(getenv("VIDDUMP") && d){ fprintf(stderr,"VID F%05u %u:",g_fr,h);
    for(unsigned y=0;y<h;y++){ unsigned v; if(pixfmt==1) v=((const unsigned*)((const char*)d+y*p))[w/2]&0xffffff; else v=((const unsigned short*)((const char*)d+y*p))[w/2]; fprintf(stderr," %x",v);} fprintf(stderr,"\n"); }
  const char*sh=getenv("SHOTS"); if(!sh||!d) return; char key[32]; sprintf(key,",%u,",g_fr); char buf[512]; sprintf(buf,",%s,",sh);
  if(!strstr(buf,key)) return; char fn[64]; sprintf(fn,"shot_%05u.ppm",g_fr); FILE*f=fopen(fn,"wb"); fprintf(f,"P6 %u %u 255\n",w,h);
  for(unsigned y=0;y<h;y++) for(unsigned x=0;x<w;x++){ unsigned char c[3];
    if(pixfmt==1){ unsigned v=((const unsigned*)((const char*)d+y*p))[x]; c[0]=v>>16;c[1]=v>>8;c[2]=v; }
    else { unsigned v=((const unsigned short*)((const char*)d+y*p))[x]; c[0]=(v>>11)<<3;c[1]=((v>>5)&63)<<2;c[2]=(v&31)<<3; }
    fwrite(c,1,3,f);} fclose(f); fprintf(stderr,"saved %s (%ux%u)\n",fn,w,h); }
static void aud(int16_t l,int16_t r){}
static size_t audb(const int16_t*d,size_t f){return f;}
static void ipoll(void){}
 static int press_from=-1, press_to=-1, press_id=-1;
static int16_t ist(unsigned port,unsigned dev,unsigned idx,unsigned id){
  if(port==0 && (int)id==press_id && (int)g_fr>=press_from && (int)g_fr<press_to) return 1;
  static int np=-1; static int pid[200000], pf[200000], pt[200000];
  if(np<0){ np=0; const char*q=getenv("PRESSSEQ");
    if(q){ char*b=strdup(q); for(char*t=strtok(b,","); t && np<200000; t=strtok(NULL,",")) if(sscanf(t,"%d:%d:%d",&pid[np],&pf[np],&pt[np])==3) np++; free(b); }
    const char*fn=getenv("PRESSFILE"); if(fn){ FILE*f=fopen(fn,"r"); while(f && np<200000 && fscanf(f,"%d %d %d",&pid[np],&pf[np],&pt[np])==3) np++; if(f) fclose(f); } }
  if(port==0) for(int k=0;k<np;k++) if((int)id==pid[k] && (int)g_fr>=pf[k] && (int)g_fr<pt[k]) return 1;
  return 0;}
int main(int argc,char**argv){
  // fe core.so sysdir bios game.gb frames [reset_at_frame] [press_id from to]
  void*h=dlopen(argv[1],RTLD_NOW); if(!h){fprintf(stderr,"%s\n",dlerror());return 1;}
  sysdir=argv[2]; bios=argv[3]; int frames=atoi(argv[5]); int reset_at = argc>6?atoi(argv[6]):-1;
  if(argc>9){press_id=atoi(argv[7]);press_from=atoi(argv[8]);press_to=atoi(argv[9]);}
#define S(n) typeof(&n) p_##n = (typeof(&n))dlsym(h,#n)
  S(retro_set_environment);S(retro_set_video_refresh);S(retro_set_audio_sample);S(retro_set_audio_sample_batch);
  S(retro_set_input_poll);S(retro_set_input_state);S(retro_init);S(retro_load_game);S(retro_run);S(retro_reset);S(retro_get_region);
  p_retro_set_environment(env);p_retro_init();
  p_retro_set_video_refresh(vid);p_retro_set_audio_sample(aud);p_retro_set_audio_sample_batch(audb);
  p_retro_set_input_poll(ipoll);p_retro_set_input_state(ist);
  struct retro_game_info gi={argv[4],NULL,0,NULL};
  if(!p_retro_load_game(&gi)){fprintf(stderr,"load failed\n");return 1;}
  fprintf(stderr,"region=%s\n",p_retro_get_region()==0?"NTSC":"PAL");
  for(g_fr=1;(int)g_fr<=frames;g_fr++){ { char rk[32]; sprintf(rk,",%u,",g_fr); char rb[256]; snprintf(rb,256,",%s,",getenv("RESETS")?getenv("RESETS"):""); if(strstr(rb,rk)) { fprintf(stderr,"=== SNES RESET at frame %u ===\n",g_fr); p_retro_reset(); } }
    if((int)g_fr==reset_at){fprintf(stderr,"=== SNES RESET at frame %u ===\n",g_fr);p_retro_reset();} p_retro_run(); }
  return 0;
}
