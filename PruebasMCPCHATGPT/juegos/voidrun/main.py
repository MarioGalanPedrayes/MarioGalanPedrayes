"""VOIDRUN: SECTOR 9 — original Python/Pygame arcade roguelite for Pygbag."""
import asyncio
import math
import random
import sys
import pygame

WIDTH, HEIGHT = 960, 600
FPS = 60
Vec = pygame.Vector2
WHITE = (235, 245, 255)
CYAN = (66, 235, 255)
PINK = (255, 70, 170)
PURPLE = (145, 95, 255)
GOLD = (255, 207, 91)
BG = (7, 10, 24)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("VOIDRUN: SECTOR 9")
clock = pygame.time.Clock()
FONT = pygame.font.Font(None, 24)
SMALL = pygame.font.Font(None, 19)
MED = pygame.font.Font(None, 34)
BIG = pygame.font.Font(None, 76)
TITLE = pygame.font.Font(None, 92)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def vec_angle(v):
    return math.atan2(v.y, v.x)

def draw_text(surface, text, font, color, pos, center=False):
    image = font.render(str(text), True, color)
    rect = image.get_rect()
    rect.center = pos if center else rect.topleft
    if not center:
        rect.topleft = pos
    surface.blit(image, rect)
    return rect

def panel(surface, rect, fill=(13, 19, 39), border=(41, 77, 111), radius=12, width=2):
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, width, border_radius=radius)

def bar(surface, x, y, w, h, value, maximum, color, back=(26, 35, 55)):
    pygame.draw.rect(surface, back, (x, y, w, h), border_radius=h//2)
    if maximum > 0:
        pygame.draw.rect(surface, color, (x, y, int(w*clamp(value/maximum, 0, 1)), h), border_radius=h//2)

class Starfield:
    def __init__(self):
        self.stars = [(random.randrange(WIDTH), random.randrange(HEIGHT), random.choice((1,1,1,2)), random.uniform(7, 28)) for _ in range(100)]
        self.grid_offset = 0
    def update(self, dt):
        self.grid_offset = (self.grid_offset + 16*dt) % 48
        self.stars = [(x, (y+speed*dt) % HEIGHT, size, speed) for x,y,size,speed in self.stars]
    def draw(self, surf):
        for x,y,size,_ in self.stars:
            pygame.draw.circle(surf, (45, 68, 96), (int(x), int(y)), size)
        for x in range(0, WIDTH, 48):
            pygame.draw.line(surf, (12, 21, 39), (x, 0), (x, HEIGHT), 1)
        for y in range(-48, HEIGHT+48, 48):
            yy = int(y + self.grid_offset)
            pygame.draw.line(surf, (12, 21, 39), (0, yy), (WIDTH, yy), 1)

class Particle:
    def __init__(self, pos, color, speed=None, life=None, radius=None):
        self.pos = Vec(pos)
        angle = random.random()*math.tau
        velocity = random.uniform(35, 210) if speed is None else speed
        self.vel = Vec(math.cos(angle), math.sin(angle))*velocity
        self.life = random.uniform(.2,.55) if life is None else life
        self.max_life = self.life
        self.radius = random.randint(2,5) if radius is None else radius
        self.color = color
    def update(self, dt):
        self.pos += self.vel*dt
        self.vel *= max(0, 1-3*dt)
        self.life -= dt
    def draw(self, surf):
        if self.life > 0:
            r = max(1, int(self.radius*self.life/self.max_life))
            pygame.draw.circle(surf, self.color, (int(self.pos.x),int(self.pos.y)), r)

class Bullet:
    def __init__(self, pos, direction, damage, speed=560, color=CYAN, radius=5, pierce=0, friendly=True):
        self.pos = Vec(pos)
        self.vel = Vec(direction).normalize()*speed
        self.damage = damage
        self.color = color
        self.radius = radius
        self.pierce = pierce
        self.friendly = friendly
        self.life = 1.5
        self.hit_ids = set()
    def update(self, dt):
        self.pos += self.vel*dt
        self.life -= dt
    def draw(self, surf):
        tail = self.pos - self.vel.normalize()*12
        pygame.draw.line(surf, self.color, tail, self.pos, self.radius*2)
        pygame.draw.circle(surf, WHITE, (int(self.pos.x),int(self.pos.y)), max(1,self.radius-2))

class Orb:
    def __init__(self, pos, value=1, kind='xp'):
        self.pos = Vec(pos)
        self.value = value
        self.kind = kind
        self.radius = 7 if kind == 'xp' else 9
        self.phase = random.random()*math.tau
    def update(self, dt, player):
        self.phase += dt*4
        delta = player.pos-self.pos
        if delta.length() < getattr(player, 'magnet', 125) and delta.length_squared() > 0:
            self.pos += delta.normalize()*(230*dt)
    def draw(self, surf):
        color = PURPLE if self.kind == 'xp' else GOLD
        p = (int(self.pos.x), int(self.pos.y))
        pygame.draw.circle(surf, color, p, self.radius+2, 1)
        pygame.draw.circle(surf, WHITE if self.kind=='heal' else color, p, self.radius-2)

class Enemy:
    TYPES = {
        'drone': {'hp':22,'speed':92,'damage':10,'radius':13,'color':(255,82,125),'xp':2},
        'stalker': {'hp':34,'speed':142,'damage':13,'radius':16,'color':(255,145,74),'xp':3},
        'tank': {'hp':100,'speed':48,'damage':22,'radius':24,'color':(178,92,255),'xp':7},
        'sniper': {'hp':28,'speed':65,'damage':12,'radius':15,'color':(255,220,100),'xp':4},
        'boss': {'hp':760,'speed':55,'damage':28,'radius':43,'color':(255,55,170),'xp':35},
    }
    def __init__(self, kind, pos, wave):
        self.kind = kind
        data = self.TYPES[kind]
        self.pos = Vec(pos)
        scale = 1 + max(0,wave-1)*.105
        self.max_hp = data['hp']*scale
        self.hp = self.max_hp
        self.speed = data['speed']*(1+min(wave*.018,.45))
        self.damage = data['damage']*(1+max(0,wave-1)*.055)
        self.radius = data['radius']
        self.color = data['color']
        self.xp = data['xp']
        self.shoot_timer = random.uniform(.8,1.8)
        self.phase = random.random()*math.tau
        self.hit_flash = 0
        self.boss = kind == 'boss'
    def update(self, dt, player, enemy_bullets):
        self.phase += dt*3
        self.hit_flash = max(0,self.hit_flash-dt)
        delta = player.pos-self.pos
        distance = max(1,delta.length())
        direction = delta/distance
        if self.kind == 'sniper':
            if distance > 290: self.pos += direction*self.speed*dt
            elif distance < 210: self.pos -= direction*self.speed*dt
            self.shoot_timer -= dt
            if self.shoot_timer <= 0:
                enemy_bullets.append(Bullet(self.pos, direction, self.damage, 290, (255,205,85), 6, friendly=False))
                self.shoot_timer = 2.0
        elif self.kind == 'boss':
            if distance > 205: self.pos += direction*self.speed*dt
            else: self.pos += Vec(-direction.y,direction.x)*math.sin(self.phase)*self.speed*.75*dt
            self.shoot_timer -= dt
            if self.shoot_timer <= 0:
                base = vec_angle(direction)
                for offset in (-.55,-.28,0,.28,.55):
                    a = base+offset
                    enemy_bullets.append(Bullet(self.pos, (math.cos(a),math.sin(a)), self.damage*.62, 245, PINK, 7, friendly=False))
                self.shoot_timer = 1.15
        else:
            self.pos += direction*self.speed*dt
            if self.kind == 'stalker':
                self.pos += Vec(-direction.y,direction.x)*math.sin(self.phase*2)*24*dt
    def draw(self, surf):
        p=(int(self.pos.x),int(self.pos.y))
        color=WHITE if self.hit_flash>0 else self.color
        if self.kind == 'boss':
            pygame.draw.circle(surf,(80,22,76),p,self.radius+10,2)
            pygame.draw.circle(surf,color,p,self.radius,3)
            pygame.draw.circle(surf,(24,12,37),p,int(self.radius*.66))
            for a in range(0,360,45):
                rad=math.radians(a)+self.phase*.2
                q=(int(self.pos.x+math.cos(rad)*(self.radius+5)),int(self.pos.y+math.sin(rad)*(self.radius+5)))
                pygame.draw.circle(surf,color,q,5)
            pygame.draw.circle(surf,WHITE,p,8)
        elif self.kind == 'tank':
            pygame.draw.polygon(surf,color,[(p[0],p[1]-self.radius),(p[0]+self.radius,p[1]),(p[0],p[1]+self.radius),(p[0]-self.radius,p[1])])
            pygame.draw.circle(surf,(35,19,53),p,8)
        elif self.kind == 'sniper':
            pygame.draw.circle(surf,color,p,self.radius,2)
            pygame.draw.line(surf,color,(p[0]-self.radius,p[1]),(p[0]+self.radius,p[1]),3)
            pygame.draw.line(surf,color,(p[0],p[1]-self.radius),(p[0],p[1]+self.radius),3)
        else:
            pygame.draw.circle(surf,color,p,self.radius)
            pygame.draw.circle(surf,(40,15,35),p,max(3,self.radius//3))
            pygame.draw.circle(surf,WHITE,(p[0]-4,p[1]-3),2)
            pygame.draw.circle(surf,WHITE,(p[0]+4,p[1]-3),2)
        if self.hp < self.max_hp:
            bar(surf,p[0]-self.radius,p[1]-self.radius-10,self.radius*2,4,self.hp,self.max_hp,(255,90,120),(55,30,48))

class Player:
    def __init__(self):
        self.pos=Vec(WIDTH/2,HEIGHT/2)
        self.radius=15
        self.hp=100;self.max_hp=100
        self.speed=250
        self.damage=19
        self.fire_rate=3.4
        self.fire_timer=0
        self.bullet_speed=570
        self.pierce=0
        self.multishot=1
        self.xp=0;self.level=1;self.next_xp=12
        self.kills=0
        self.dash_cd=0;self.dash_time=0
        self.pulse_cd=0
        self.invulnerable=0
        self.weapons={'pulse rifle':1,'arc drone':0,'nova':0}
        self.drone_timer=0
        self.aim=Vec(1,0)
    def update(self,dt,keys,mouse_pos,bullets,particles):
        move=Vec(0,0)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:move.x-=1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:move.x+=1
        if keys[pygame.K_w] or keys[pygame.K_UP]:move.y-=1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:move.y+=1
        if move.length_squared()>0:
            move=move.normalize();self.pos+=move*self.speed*dt
        self.pos.x=clamp(self.pos.x,self.radius+8,WIDTH-self.radius-8)
        self.pos.y=clamp(self.pos.y,self.radius+8,HEIGHT-self.radius-8)
        aim=Vec(mouse_pos)-self.pos
        if aim.length_squared()>0:self.aim=aim.normalize()
        self.fire_timer-=dt;self.dash_cd=max(0,self.dash_cd-dt);self.pulse_cd=max(0,self.pulse_cd-dt)
        self.dash_time=max(0,self.dash_time-dt);self.invulnerable=max(0,self.invulnerable-dt)
        self.drone_timer-=dt
    def shoot(self, target, bullets):
        if self.fire_timer>0:return
        direction=Vec(target)-self.pos
        if direction.length_squared()<1:return
        direction=direction.normalize();self.aim=direction
        base=vec_angle(direction)
        count=self.multishot
        for i in range(count):
            spread=(i-(count-1)/2)*.13
            a=base+spread
            d=Vec(math.cos(a),math.sin(a))
            bullets.append(Bullet(self.pos+d*20,d,self.damage,self.bullet_speed,CYAN,5,self.pierce))
        self.fire_timer=1/self.fire_rate
    def dash(self, keys, particles):
        if self.dash_cd>0:return
        move=Vec(0,0)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:move.x-=1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:move.x+=1
        if keys[pygame.K_w] or keys[pygame.K_UP]:move.y-=1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:move.y+=1
        if move.length_squared()==0:move=self.aim
        else:move=move.normalize()
        self.pos+=move*112
        self.pos.x=clamp(self.pos.x,self.radius+8,WIDTH-self.radius-8)
        self.pos.y=clamp(self.pos.y,self.radius+8,HEIGHT-self.radius-8)
        self.invulnerable=.36;self.dash_cd=3.2
        for _ in range(12):particles.append(Particle(self.pos,PURPLE))
    def pulse(self, enemies, particles):
        if self.pulse_cd>0:return
        self.pulse_cd=8
        for e in enemies:
            d=e.pos-self.pos
            if d.length()<165:
                e.hp-=72
                if d.length_squared():e.pos+=d.normalize()*65
        for _ in range(34):particles.append(Particle(self.pos,CYAN,life=.42))
    def draw(self,surf):
        p=(int(self.pos.x),int(self.pos.y))
        if self.invulnerable>0 and int(self.invulnerable*22)%2==0:return
        pygame.draw.circle(surf,(17,67,92),p,25,2)
        pygame.draw.circle(surf,CYAN,p,self.radius)
        tip=self.pos+self.aim*23
        pygame.draw.line(surf,WHITE,self.pos,tip,4)
        pygame.draw.circle(surf,(7,20,36),p,6)
        pygame.draw.circle(surf,WHITE,(int(self.pos.x-4),int(self.pos.y-3)),2)
        pygame.draw.circle(surf,WHITE,(int(self.pos.x+4),int(self.pos.y-3)),2)

UPGRADES = [
    ('overclock','SOBRECARGA','+22% cadencia de disparo','fire'),
    ('heavy','NÚCLEO PESADO','+35% daño por proyectil','damage'),
    ('thrusters','TURBO VECTORIAL','+12% velocidad de movimiento','speed'),
    ('multishot','DOBLE DESCARGA','Añade un proyectil extra','multi'),
    ('pierce','FASE FANTASMA','Los disparos atraviesan enemigos','pierce'),
    ('hull','BLINDAJE','+25 vida máxima y recuperación','hull'),
    ('drone','DRON DE COMBATE','Un dron dispara automáticamente','drone'),
    ('nova','NOVA','Activa una explosión automática periódica','nova'),
    ('magnet','IMÁN CUÁNTICO','Aumenta el alcance de recogida','magnet'),
    ('repair','NANORREPARACIÓN','Recupera 35 puntos de vida','heal'),
]

class Game:
    def __init__(self):
        self.state='menu';self.starfield=Starfield();self.reset()
        self.high_score=0
        if sys.platform == 'emscripten':
            try:self.high_score=int(__import__('platform').window.localStorage.getItem('voidrun-best') or 0)
            except Exception:self.high_score=0
    def reset(self):
        self.player=Player();self.enemies=[];self.bullets=[];self.enemy_bullets=[];self.orbs=[];self.particles=[]
        self.elapsed=0;self.wave=1;self.wave_timer=0;self.spawn_timer=0;self.kills=0;self.score=0
        self.boss_spawned=False;self.boss_defeated=False;self.upgrade_choices=[];self.upgrade_source='level';self.notice='';self.notice_timer=0
        self.shake=0;self.combo=0;self.combo_timer=0;self.paused_from='playing'
    def start(self):self.reset();self.state='playing'
    def spawn_enemy(self):
        side=random.randrange(4)
        if side==0:pos=(random.randrange(WIDTH),-35)
        elif side==1:pos=(WIDTH+35,random.randrange(HEIGHT))
        elif side==2:pos=(random.randrange(WIDTH),HEIGHT+35)
        else:pos=(-35,random.randrange(HEIGHT))
        if self.wave%5==0 and not self.boss_spawned:
            kind='boss';self.boss_spawned=True
        else:
            roll=random.random()
            if self.wave<2:kind='drone'
            elif roll<.48:kind='drone'
            elif roll<.72:kind='stalker'
            elif roll<.89:kind='sniper'
            else:kind='tank'
        self.enemies.append(Enemy(kind,pos,self.wave))
    def choose_upgrades(self):
        self.upgrade_choices=random.sample(UPGRADES,3);self.state='upgrade'
    def apply_upgrade(self,choice):
        key=choice[0];p=self.player
        if key=='overclock':p.fire_rate*=1.22
        elif key=='heavy':p.damage*=1.35
        elif key=='thrusters':p.speed*=1.12
        elif key=='multishot':p.multishot=min(5,p.multishot+1)
        elif key=='pierce':p.pierce=min(5,p.pierce+1)
        elif key=='hull':p.max_hp+=25;p.hp=min(p.max_hp,p.hp+35)
        elif key=='drone':p.weapons['arc drone']+=1
        elif key=='nova':p.weapons['nova']+=1
        elif key=='magnet':p.magnet=getattr(p,'magnet',125)+65
        elif key=='repair':p.hp=min(p.max_hp,p.hp+35)
        self.notice=choice[2];self.notice_timer=2.2;self.state='playing'
    def damage_player(self,amount):
        p=self.player
        if p.invulnerable>0:return
        p.hp-=amount;p.invulnerable=.7;self.shake=8
        for _ in range(12):self.particles.append(Particle(p.pos,PINK))
        if p.hp<=0:self.game_over()
    def game_over(self):
        self.state='gameover';self.high_score=max(self.high_score,self.score)
        if sys.platform=='emscripten':
            try:__import__('platform').window.localStorage.setItem('voidrun-best',str(self.high_score))
            except Exception:pass
    def kill_enemy(self,e):
        if e not in self.enemies:return
        self.enemies.remove(e);self.kills+=1;self.player.kills+=1;self.score+=int(12+e.xp*3)
        self.combo+=1;self.combo_timer=2.4
        self.orbs.append(Orb(e.pos,e.xp,'xp'))
        if random.random()<.055:self.orbs.append(Orb(e.pos,1,'heal'))
        for _ in range(16 if e.boss else 7):self.particles.append(Particle(e.pos,e.color))
        if e.boss:
            self.boss_defeated=True;self.score+=500;self.notice='JEFE ELIMINADO · +500';self.notice_timer=3
            for _ in range(3):self.orbs.append(Orb(e.pos,1,'heal'))
    def collect_xp(self,orb):
        p=self.player
        if orb.kind=='heal':p.hp=min(p.max_hp,p.hp+18);return
        p.xp+=orb.value
        while p.xp>=p.next_xp:
            p.xp-=p.next_xp;p.level+=1;p.next_xp=int(p.next_xp*1.32+5);self.score+=100
            self.upgrade_source='level';self.choose_upgrades();break
    def update(self,dt,keys,mouse_pos,mouse_down):
        self.starfield.update(dt)
        if self.state!='playing':
            for particle in self.particles:particle.update(dt)
            self.particles=[x for x in self.particles if x.life>0]
            return
        self.elapsed+=dt;self.wave_timer+=dt;self.spawn_timer-=dt
        self.notice_timer=max(0,self.notice_timer-dt);self.shake=max(0,self.shake-25*dt)
        self.combo_timer=max(0,self.combo_timer-dt)
        if self.combo_timer==0:self.combo=0
        p=self.player;p.update(dt,keys,mouse_pos,self.bullets,self.particles)
        if mouse_down:self.player.shoot(mouse_pos,self.bullets)
        elif self.enemies:
            target=min(self.enemies,key=lambda e:(e.pos-p.pos).length_squared())
            self.player.shoot(target.pos,self.bullets)
        if keys[pygame.K_SPACE] and p.dash_cd<=0:p.dash(keys,self.particles)
        if keys[pygame.K_q] and p.pulse_cd<=0:p.pulse(self.enemies,self.particles)
        if p.weapons['arc drone'] and p.drone_timer<=0 and self.enemies:
            target=min(self.enemies,key=lambda e:(e.pos-p.pos).length_squared())
            d=target.pos-p.pos
            if d.length_squared():self.bullets.append(Bullet(p.pos,d,11*p.weapons['arc drone'],470,PURPLE,4,1))
            p.drone_timer=max(.22,.85/(1+.25*(p.weapons['arc drone']-1)))
        if p.weapons['nova']:
            p.nova_timer=getattr(p,'nova_timer',0)-dt
            if p.nova_timer<=0:
                for e in self.enemies:
                    if (e.pos-p.pos).length()<205:e.hp-=48*p.weapons['nova']
                for _ in range(24):self.particles.append(Particle(p.pos,PINK,life=.38))
                p.nova_timer=max(2.8,7/(1+.2*(p.weapons['nova']-1)))
        spawn_rate=max(.34,1.35-self.wave*.055)
        if self.spawn_timer<=0 and len(self.enemies)<min(38,7+self.wave*2):
            self.spawn_enemy();self.spawn_timer=spawn_rate
        if self.wave_timer>=34:
            self.wave_timer=0;self.wave+=1;self.boss_spawned=False;self.notice='OLEADA '+str(self.wave);self.notice_timer=2
            p.hp=min(p.max_hp,p.hp+8)
        for e in list(self.enemies):
            e.update(dt,p,self.enemy_bullets)
            if (e.pos-p.pos).length()<e.radius+p.radius:
                self.damage_player(e.damage*dt*2.4)
                d=p.pos-e.pos
                if d.length_squared():p.pos+=d.normalize()*95*dt
        for b in list(self.bullets):
            b.update(dt)
            if b.life<=0 or not (-40<b.pos.x<WIDTH+40 and -40<b.pos.y<HEIGHT+40):
                if b in self.bullets:self.bullets.remove(b)
                continue
            for e in list(self.enemies):
                if id(e) in b.hit_ids:continue
                if (e.pos-b.pos).length()<e.radius+b.radius:
                    e.hp-=b.damage;e.hit_flash=.09;b.hit_ids.add(id(e))
                    for _ in range(3):self.particles.append(Particle(b.pos,b.color,speed=80,life=.18,radius=2))
                    if e.hp<=0:self.kill_enemy(e)
                    if b.pierce>0:b.pierce-=1
                    else:
                        if b in self.bullets:self.bullets.remove(b)
                        break
        for b in list(self.enemy_bullets):
            b.update(dt)
            if b.life<=0 or not (-30<b.pos.x<WIDTH+30 and -30<b.pos.y<HEIGHT+30):
                if b in self.enemy_bullets:self.enemy_bullets.remove(b)
                continue
            if (b.pos-p.pos).length()<p.radius+b.radius:
                self.damage_player(b.damage)
                if b in self.enemy_bullets:self.enemy_bullets.remove(b)
        for orb in list(self.orbs):
            orb.update(dt,p)
            if (orb.pos-p.pos).length()<p.radius+orb.radius+4:
                self.collect_xp(orb);self.orbs.remove(orb)
        for particle in self.particles:particle.update(dt)
        self.particles=[x for x in self.particles if x.life>0]
        self.bullets=[b for b in self.bullets if b.life>0]
        self.enemy_bullets=[b for b in self.enemy_bullets if b.life>0]
    def draw_world(self,surf):
        self.starfield.draw(surf)
        for orb in self.orbs:orb.draw(surf)
        for b in self.bullets:b.draw(surf)
        for b in self.enemy_bullets:b.draw(surf)
        for e in self.enemies:e.draw(surf)
        self.player.draw(surf)
        for part in self.particles:part.draw(surf)
    def draw_hud(self,surf):
        p=self.player
        panel(surf,(16,14,265,78),(9,17,34),(31,74,99),10)
        draw_text(surf,'CASCO',SMALL,(154,179,202),(29,22));draw_text(surf,f'{max(0,int(p.hp))}/{p.max_hp}',FONT,WHITE,(29,43))
        bar(surf,29,68,235,9,p.hp,p.max_hp,(255,74,124))
        panel(surf,(WIDTH-228,14,212,78),(9,17,34),(31,74,99),10)
        draw_text(surf,'SECTOR 09',SMALL,(154,179,202),(WIDTH-211,22))
        draw_text(surf,f'OLEADA {self.wave:02d}',MED,CYAN,(WIDTH-211,40))
        draw_text(surf,f'{int(self.elapsed//60):02d}:{int(self.elapsed%60):02d}',FONT,WHITE,(WIDTH-70,48))
        draw_text(surf,f'NIVEL {p.level}',SMALL,GOLD,(WIDTH//2-90,17))
        bar(surf,WIDTH//2-90,38,180,8,p.xp,p.next_xp,PURPLE)
        draw_text(surf,f'{int(p.xp)}/{p.next_xp} XP',SMALL,(174,185,220),(WIDTH//2-90,51))
        for i,(label,ready,clr) in enumerate((('ESPACIO',p.dash_cd<=0,PURPLE),('Q',p.pulse_cd<=0,CYAN))):
            x=WIDTH//2-76+i*91
            pygame.draw.rect(surf,(22,28,50),(x,HEIGHT-46,82,31),border_radius=7)
            pygame.draw.rect(surf,clr if ready else (67,75,96),(x,HEIGHT-46,82,31),2,border_radius=7)
            draw_text(surf,label,SMALL,WHITE,(x+41,HEIGHT-31),True)
        draw_text(surf,f'✦ {self.score:,}',FONT,GOLD,(WIDTH-115,HEIGHT-37))
        draw_text(surf,f'ELIMINADOS {self.kills}',SMALL,(157,179,204),(18,HEIGHT-29))
        bosses=[e for e in self.enemies if e.boss]
        if bosses:
            boss=bosses[0];draw_text(surf,'NÚCLEO TITÁN',SMALL,PINK,(WIDTH//2,90),True)
            bar(surf,WIDTH//2-170,108,340,10,boss.hp,boss.max_hp,PINK,(57,20,50))
        if self.combo>2 and self.combo_timer>0:draw_text(surf,f'{self.combo}x COMBO',MED,GOLD,(WIDTH//2,142),True)
        if self.notice_timer>0:draw_text(surf,self.notice,MED,CYAN,(WIDTH//2,HEIGHT-88),True)
    def draw_menu(self,surf):
        self.starfield.draw(surf)
        t=pygame.time.get_ticks()/1000
        for r in (95,135,178):pygame.draw.circle(surf,(22,65,91),(WIDTH//2,245),r,1)
        pygame.draw.circle(surf,CYAN,(WIDTH//2,245),18+int(3*math.sin(t*3)),2)
        draw_text(surf,'VOIDRUN',TITLE,WHITE,(WIDTH//2,140),True)
        draw_text(surf,'SECTOR 09',MED,CYAN,(WIDTH//2,320),True)
        draw_text(surf,'SOBREVIVE. MEJORA. ROMPE EL CICLO.',FONT,(174,194,220),(WIDTH//2,366),True)
        panel(surf,(WIDTH//2-160,414,320,54),(13,29,48),(44,156,183),10)
        draw_text(surf,'PULSA ENTER O TOCA PARA JUGAR',FONT,WHITE,(WIDTH//2,441),True)
        draw_text(surf,'WASD / FLECHAS · AUTO-DISPARO · ESPACIO DASH · Q PULSO · ESC PAUSA',SMALL,(142,162,188),(WIDTH//2,500),True)
        draw_text(surf,f'RECORD LOCAL  {self.high_score:,}',SMALL,GOLD,(WIDTH//2,538),True)
    def draw_upgrade(self,surf):
        overlay=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA);overlay.fill((3,6,17,205));surf.blit(overlay,(0,0))
        draw_text(surf,'NUEVA SINCRONIZACIÓN',BIG,WHITE,(WIDTH//2,150),True)
        draw_text(surf,'ELIGE UNA MEJORA PARA TU NÚCLEO',FONT,CYAN,(WIDTH//2,195),True)
        for i,c in enumerate(self.upgrade_choices):
            x=WIDTH//2-355+i*240;rect=pygame.Rect(x,250,215,205)
            panel(surf,rect,(14,24,47),(53,137,166),14)
            pygame.draw.circle(surf,(20,64,86),(x+107,295),24,2)
            draw_text(surf,str(i+1),MED,CYAN,(x+107,295),True)
            draw_text(surf,c[1],FONT,WHITE,(x+107,345),True)
            words=c[2].split();line='';yy=380
            for word in words:
                test=(line+' '+word).strip()
                if FONT.size(test)[0]>175:
                    draw_text(surf,line,SMALL,(166,190,215),(x+107,yy),True);yy+=21;line=word
                else:line=test
            if line:draw_text(surf,line,SMALL,(166,190,215),(x+107,yy),True)
            draw_text(surf,'SELECCIONAR',SMALL,GOLD,(x+107,426),True)
        draw_text(surf,'Pulsa 1, 2 o 3',SMALL,(139,157,183),(WIDTH//2,490),True)
    def draw_pause(self,surf):
        overlay=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA);overlay.fill((3,6,17,190));surf.blit(overlay,(0,0))
        draw_text(surf,'PAUSA',BIG,WHITE,(WIDTH//2,235),True)
        draw_text(surf,'Pulsa ESC para continuar',FONT,CYAN,(WIDTH//2,300),True)
        draw_text(surf,'Tu sector espera.',SMALL,(155,173,197),(WIDTH//2,337),True)
    def draw_gameover(self,surf):
        overlay=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA);overlay.fill((5,5,16,220));surf.blit(overlay,(0,0))
        draw_text(surf,'SEÑAL PERDIDA',BIG,PINK,(WIDTH//2,180),True)
        draw_text(surf,'La estación ha caído.',FONT,(182,196,217),(WIDTH//2,225),True)
        draw_text(surf,f'{self.score:,}',TITLE,WHITE,(WIDTH//2,300),True)
        draw_text(surf,'PUNTUACIÓN FINAL',SMALL,CYAN,(WIDTH//2,350),True)
        draw_text(surf,f'ELIMINADOS {self.kills}     NIVEL {self.player.level}     OLEADA {self.wave}',FONT,(178,193,214),(WIDTH//2,400),True)
        draw_text(surf,f'RECORD {self.high_score:,}',MED,GOLD,(WIDTH//2,450),True)
        panel(surf,(WIDTH//2-155,490,310,48),(14,35,53),(52,155,183),9)
        draw_text(surf,'ENTER / TOCAR PARA REINTENTAR',FONT,WHITE,(WIDTH//2,514),True)
    def draw(self):
        frame=pygame.Surface((WIDTH,HEIGHT));frame.fill(BG)
        if self.state=='menu':self.draw_menu(frame)
        else:
            self.draw_world(frame);self.draw_hud(frame)
            if self.state=='upgrade':self.draw_upgrade(frame)
            elif self.state=='paused':self.draw_pause(frame)
            elif self.state=='gameover':self.draw_gameover(frame)
        if self.shake>0 and self.state=='playing':
            ox=random.randint(-int(self.shake),int(self.shake));oy=random.randint(-int(self.shake),int(self.shake))
        else:ox=oy=0
        screen.fill(BG);screen.blit(frame,(ox,oy));pygame.display.flip()

game=Game()

def handle_click(pos):
    if game.state=='menu':game.start();return
    if game.state=='gameover':game.start();return
    if game.state=='upgrade':
        for i in range(3):
            x=WIDTH//2-355+i*240
            if pygame.Rect(x,250,215,205).collidepoint(pos):game.apply_upgrade(game.upgrade_choices[i]);return

async def main():
    running=True
    while running:
        dt=min(clock.tick(FPS)/1000,0.035)
        keys=pygame.key.get_pressed()
        mouse_pos=pygame.mouse.get_pos()
        mouse_down=pygame.mouse.get_pressed()[0]
        for event in pygame.event.get():
            if event.type==pygame.QUIT:running=False
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    if game.state=='playing':game.state='paused'
                    elif game.state=='paused':game.state='playing'
                elif game.state=='menu' and event.key in (pygame.K_RETURN,pygame.K_SPACE):game.start()
                elif game.state=='gameover' and event.key in (pygame.K_RETURN,pygame.K_SPACE):game.start()
                elif game.state=='upgrade' and event.key in (pygame.K_1,pygame.K_2,pygame.K_3):game.apply_upgrade(game.upgrade_choices[event.key-pygame.K_1])
                elif game.state=='playing' and event.key==pygame.K_q:game.player.pulse(game.enemies,game.particles)
                elif game.state=='playing' and event.key==pygame.K_SPACE:game.player.dash(keys,game.particles)
            elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                if game.state in ('menu','gameover','upgrade'):handle_click(event.pos)
        if game.state=='playing':game.update(dt,keys,mouse_pos,mouse_down)
        else:game.update(dt,keys,mouse_pos,False)
        game.draw()
        await asyncio.sleep(0)

asyncio.run(main())
