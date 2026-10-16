#!/usr/bin/env python3
"""Stage9c2 persistent80-entry highscore manager; separate from stable gameplay."""
import argparse,hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
import build_stage3b1 as DISK
ROOT=Path(__file__).resolve().parents[1]
BASE='4acc8a2ed958f933dc3af9d9220c250b005a813c'
TITLE='- VYPER HIGH SCORE TABLE -'
FOOTER='- PRESS A KEY OR JOYSTICK BUTTON TO CONTINUE -'
COLS=(16,49);ROWS=range(7,17);WIDTH=15

def screen_code(c):
    n=ord(c)
    if 64<=n<=95:return n-64
    if 32<=n<=63:return n
    raise ValueError('Unsupported screen character '+c)
def assets():
    # These are intentionally invented, deterministic test names, never original scores.
    names=('ACE','B02','K-9','7UP','A+B','X/Y','!?!','Z9Z','M.R','Q@1')
    entries=[{'rank':i,'name':names[(i-1)%len(names)],'score':(81-i)**3-1} for i in range(1,81)]
    pages=[];colours=bytearray([1]*2000)
    def put(screen,x,y,text,colour=1):
        assert 0<=x and x+len(text)<=80 and 0<=y<25
        for k,c in enumerate(text):screen[80*y+x+k]=screen_code(c);colours[80*y+x+k]=colour
    for page in range(4):
        screen=bytearray([32]*2000)
        for x in range(5,75):
            screen[80+x]=128;screen[23*80+x]=128
        for y in range(2,23):screen[y*80+4]=129;screen[y*80+75]=129
        for x,y,glyph in ((4,1,130),(75,1,131),(4,23,132),(75,23,133)):screen[y*80+x]=glyph
        for i,v in enumerate(screen):
            if v>=128:colours[i]=2
        put(screen,(80-len(TITLE))//2,3,TITLE,2)
        put(screen,(80-len(FOOTER))//2,21,FOOTER,2)
        put(screen,16,5,'RANK NAME SCORE');put(screen,49,5,'RANK NAME SCORE')
        put(screen,30,18,f'PAGE {page+1}/4 - TEST DATA')
        hint='CURSOR / JOYSTICK LEFT-RIGHT: PAGE'
        put(screen,(80-len(hint))//2,19,hint)
        for col,x in enumerate(COLS):
            for row,y in enumerate(ROWS):
                e=entries[page*20+col*10+row]
                text=f"{e['rank']:02d}: {e['name']} {e['score']:7d}"
                assert len(text)==WIDTH
                put(screen,x,y,text,3+row%3)
        pages.append(bytes(screen))
    # Six thin frame tiles in a runtime copy of the real MEGA65 character WOM.
    frame=bytes([0,0,0,255,0,0,0,0]+[16]*8+
                [0,0,0,31,16,16,16,16]+[0,0,0,240,16,16,16,16]+
                [16,16,16,31,0,0,0,0]+[16,16,16,240,0,0,0,0])
    return pages,bytes(colours),frame,entries

def protect():
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--','src','assets','tools','releases'],cwd=ROOT,text=True).splitlines()
    for p in paths:
        if (ROOT/p).read_bytes()!=subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT):raise ValueError('Stable changed: '+p)
    return len(paths)
def build(jar,output):
    jar=Path(jar).resolve();output=Path(output).resolve()
    if DISK.sha(jar.read_bytes())!=DISK.KICKASS_SHA256:raise ValueError('KickAssembler5.25 required')
    if output.is_relative_to(ROOT/'releases') and not output.is_relative_to(ROOT/'releases/stage_9c2'):raise ValueError('Protected release destination')
    count=protect();pages,colours,frame,entries=assets()
    import highscore_format as FORMAT
    blank=bytearray(pages[0])
    # Clear only the interior: whole-row clearing erased both frame columns.
    for y in ROWS:blank[y*80+5:y*80+75]=bytes([32])*70
    for y in (17,18,19):blank[y*80:(y+1)*80]=bytes([32])*80;blank[y*80+4]=129;blank[y*80+75]=129
    for x in COLS:
        header='RANK NAME    SCORE'
        blank[80*5+x:80*5+x+18]=bytes(screen_code(c) for c in header)
    pages=[bytes(blank)]
    colours=bytearray(colours)
    for row in range(10):
        for x in COLS:colours[80*(7+row)+x:80*(7+row)+x+18]=bytes([3+row%3])*18
    colours=bytes(colours);entries=[];packet=FORMAT.encode([])
    with tempfile.TemporaryDirectory(prefix='vyper-9c1-') as tmp:
        w=Path(tmp)
        for n in ('stage9c2.asm','stage9c2_video.asm','stage9c2_cycling.asm','stage9c2_data.asm','stage9c2_manage.asm','stage9c2_disk.asm'):shutil.copyfile(ROOT/'src/tests'/n,w/n)
        shutil.copyfile(ROOT/'assets/stage6a2/color_cycle.inc',w/'color_cycle.inc')
        for n,b in [('VYHI.DAT',packet),('pages.bin',b''.join(pages)),('colours.bin',colours),('frame.bin',frame)]: (w/n).write_bytes(b)
        run=subprocess.run(['java','-jar',str(jar),'stage9c2.asm','-o','STAGE9C2.PRG','-symbolfile','-showmem'],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(run.stdout,end='');run.check_returncode()
        prg=(w/'STAGE9C2.PRG').read_bytes();disk=bytearray(DISK.build_disk([('STAGE9C2',prg,0x82),('VYHI.DAT',packet,0x81)]))
        disk[39*40*256+4:39*40*256+20]=b'VYPER STAGE9C2'.ljust(16,b'\xa0');disk=bytes(disk)
        files=DISK.verify_disk(disk,[('STAGE9C2',prg,0x82),('VYHI.DAT',packet,0x81)])
        report={'stage':'9c2','issue':83,'stable':False,'base':BASE,'protected_files':count,'mode':'mono80x25,640x200,8x8 font from runtime WOM','title':TITLE,'footer':FOOTER,'columns':COLS,'entry_rows':list(ROWS),'entry_width':18,'frame':[4,1,75,23],'cycle':'unchanged Stage9b1 cc routine / Stage6a2 constants','bands':{'colours_rgb4':['00F','FF0','F00'],'direction':'up','rows_per_band':1,'frames_per_row_step':8},'pages':4,'capacity':80,'entries':0,'test_data_only':True,'storage':'VYHI v1 CRC16-CCITT, temp/readback/backup/rename; pending files preserved read-only','score':{'bytes':4,'endian':'little','maximum':4294967295,'empty_slots':'explicit occupied count'},'name_alphabet':'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-+/.@!?' ,'disk_files':files,'layout_reference':'confirmed Stage9c1 4acc8a2; score field widened to ten digits','xemu':'NOT_RUN; user acceptance required'}
        out={'STAGE9C2.PRG':prg,'STAGE9C2.sym':(w/'stage9c2.sym').read_bytes(),'VYPER_STAGE9C2.d81':disk,'test-entries.json':(json.dumps(entries,indent=2)+'\n').encode(),'build-report.json':(json.dumps(report,indent=2)+'\n').encode(),'memory-map.txt':(run.stdout[run.stdout.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode()}
        for n in ('stage9c2.asm','stage9c2_video.asm','stage9c2_cycling.asm','stage9c2_data.asm','stage9c2_manage.asm','stage9c2_disk.asm','VYHI.DAT','color_cycle.inc','pages.bin','colours.bin','frame.bin'):out[n]=(w/n).read_bytes()
        out['SHA256SUMS.txt']=''.join(f'{DISK.sha(b)}  {n}\n' for n,b in sorted(out.items())).encode()
        output.mkdir(parents=True,exist_ok=True)
        for n,b in out.items():(output/n).write_bytes(b)
    print('Protected Stable; PRG and standalone819200-byte D81 verified.')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kickass',default=os.getenv('KICKASS_JAR'));p.add_argument('--output',type=Path,default=ROOT/'releases/stage_9c2');a=p.parse_args()
    if not a.kickass:p.error('--kickass required')
    build(a.kickass,a.output)
