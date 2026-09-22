"""
오버워치(Overwatch) 스타일 3D FPS 게임 (Python + Ursina Engine)
- 주요 신규 기능:
  - 스나이퍼 조준 (ADS): 우클릭 시 4배율 광학 스코프 & 정밀 십자선 & 마우스 감도 자동 감속
  - 사람다운 1인칭 손/팔(Hands & Arms) 모델링: 양손 파지 및 대기 중 호흡(Idle) 모션
  - 찰진 5단계 택티컬 재장전(Reload): 탄창 배출 -> 새 에너지 탄창 삽입 -> 노리쇠(Bolt) 코킹
  - 사람 형태의 휴머노이드 훈련 봇: 머리, 가슴, 어깨, 양팔, 다리 및 '헤드샷(Headshot)' 치명타 판정
  - 전술 조준경 (Q 궁극기): 화면 비틀림 없는 스마트 락온 사격
  - 고대비 다크 사이버 훈련장: 선명한 바닥 격자 윤곽선 및 오브젝트 와이어프레임
"""

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.models.procedural.cylinder import Cylinder
import math
import random
import time

app = Ursina()
cylinder_model = Cylinder(resolution=16)

# --- 윈도우 창 설정 ---
window.title = "Overwatch 3D Practice Range - Sniper Edition"
window.borderless = False
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = True
window.color = color.hex('#0b0f19')

# --- 맵 환경 (고대비 다크 사이버 훈련장) ---
Sky(color=color.hex('#0b0f19'), texture=None)  # 깔끔한 다크 네이비 밤하늘
DirectionalLight(y=15, z=-10, shadows=True, color=color.hex('#ffffff'))
AmbientLight(color=color.hex('#2d3748'))

# 다크 사이버 바닥 타일
ground = Entity(
    model='plane',
    collider='box',
    scale=(120, 1, 120),
    color=color.hex('#151b27')
)

# 바닥 타일 격자 윤곽선 (가로/세로 10단위 그리드)
for z_pos in range(-50, 51, 10):
    Entity(model='cube', scale=(120, 0.02, 0.15), position=(0, 0.01, z_pos), color=color.hex('#242e42'))
for x_pos in range(-50, 51, 10):
    Entity(model='cube', scale=(0.15, 0.02, 120), position=(x_pos, 0.01, 0), color=color.hex('#242e42'))

# 바닥 네온 가이드 라인 (선명한 청록색 발광 라인)
for z_pos in [-30, 0, 30]:
    Entity(model='cube', scale=(120, 0.03, 0.4), position=(0, 0.02, z_pos), color=color.hex('#00d2d3'))
for x_pos in [-30, 0, 30]:
    Entity(model='cube', scale=(0.4, 0.03, 120), position=(x_pos, 0.02, 0), color=color.hex('#00d2d3'))

# 외곽 하이테크 방벽 (다크 메탈 + 와이어프레임 윤곽선)
wall_mat = color.hex('#1a2130')
def create_boundary_wall(pos, scale):
    w = Entity(model='cube', collider='box', position=pos, scale=scale, color=wall_mat)
    Entity(parent=w, model='wireframe_cube', scale=1.002, color=color.hex('#37455d'))

create_boundary_wall((0, 6, 60), (120, 12, 2))
create_boundary_wall((0, 6, -60), (120, 12, 2))
create_boundary_wall((60, 6, 0), (2, 12, 120))
create_boundary_wall((-60, 6, 0), (2, 12, 120))

# 벽 상단 발광 오렌지 테두리
Entity(model='cube', position=(0, 11.8, 59), scale=(120, 0.3, 0.3), color=color.hex('#fa9c1e'))
Entity(model='cube', position=(0, 11.8, -59), scale=(120, 0.3, 0.3), color=color.hex('#fa9c1e'))
Entity(model='cube', position=(59, 11.8, 0), scale=(0.3, 0.3, 120), color=color.hex('#fa9c1e'))
Entity(model='cube', position=(-59, 11.8, 0), scale=(0.3, 0.3, 120), color=color.hex('#fa9c1e'))

# 미래형 홀로그램 엄폐물 구조물 (윤곽선 와이어프레임 포함)
def create_cyber_pillar(pos):
    p = Entity(model='cube', collider='box', position=pos, scale=(4, 8, 4), color=color.hex('#1e2638'))
    Entity(parent=p, model='wireframe_cube', scale=1.003, color=color.hex('#00d2d3'))
    Entity(model='cube', position=pos, scale=(4.1, 0.4, 4.1), color=color.hex('#fa9c1e'))
    Entity(model='cube', position=(pos[0], pos[1] + 2.5, pos[2]), scale=(4.1, 0.4, 4.1), color=color.hex('#00d2d3'))

create_cyber_pillar((-18, 4, 15))
create_cyber_pillar((18, 4, 15))
create_cyber_pillar((-25, 4, -15))
create_cyber_pillar((25, 4, -15))
create_cyber_pillar((0, 4, 30))

# --- 슈퍼 점프 패드 (오버워치 Jump Pad) ---
jump_pad = Entity(
    model=cylinder_model,
    position=(0, 0.1, 0),
    scale=(5, 0.2, 5),
    color=color.hex('#1e2535')
)
Entity(parent=jump_pad, model=cylinder_model, scale=(0.8, 1.2, 0.8), color=color.hex('#fa9c1e'))
Entity(parent=jump_pad, model=cylinder_model, scale=(0.5, 1.4, 0.5), color=color.hex('#00d2d3'))

# --- 플레이어 컨트롤러 ---
player = FirstPersonController(
    model='cube',
    collider='box',
    origin_y=-0.5,
    speed=10,
    jump_height=2.0
)
player.cursor.visible = False
player_hp = 200
max_player_hp = 200

# --- 1인칭 손/팔(Hands & Arms) 및 오버워치 펄스 스나이퍼 라이플 ---
gun_holder = Entity(parent=camera, position=(0.38, -0.32, 0.65))

# 1. 사람다운 1인칭 손 & 팔 모델링 (SF 택티컬 건틀릿)
# 오른팔 (권총 손잡이 파지)
right_arm = Entity(parent=gun_holder, model='cube', scale=(0.14, 0.16, 0.5), position=(0.1, -0.22, -0.25), rotation=(15, -12, 10), color=color.hex('#1e293b'))
right_hand = Entity(parent=gun_holder, model='cube', scale=(0.13, 0.13, 0.16), position=(0.04, -0.12, -0.05), color=color.hex('#334155'))

# 왼팔 (총열 덮개 하단 든든히 지지 파지)
left_arm = Entity(parent=gun_holder, model='cube', scale=(0.13, 0.15, 0.5), position=(-0.24, -0.24, 0.05), rotation=(-20, 35, -15), color=color.hex('#1e293b'))
left_hand = Entity(parent=gun_holder, model='cube', scale=(0.12, 0.12, 0.16), position=(-0.08, -0.07, 0.25), rotation=(0, 20, 10), color=color.hex('#334155'))

# 2. 총기 본체
gun_body = Entity(parent=gun_holder, model='cube', scale=(0.14, 0.18, 0.7), color=color.hex('#e2e8f0'))
gun_top = Entity(parent=gun_holder, model='cube', scale=(0.12, 0.08, 0.6), position=(0, 0.11, -0.05), color=color.hex('#1e293b'))
gun_neon1 = Entity(parent=gun_holder, model='cube', scale=(0.145, 0.03, 0.4), position=(0, 0.02, 0.05), color=color.hex('#00d2d3'))
gun_neon2 = Entity(parent=gun_holder, model='cube', scale=(0.04, 0.03, 0.145), position=(0, 0.08, 0.18), color=color.hex('#fa9c1e'))

# 착탈식 에너지 탄창 (장전 모션용)
magazine = Entity(parent=gun_holder, model='cube', scale=(0.08, 0.22, 0.16), position=(0, -0.15, 0.08), color=color.hex('#00d2d3'))

# 스나이퍼 광학 스코프 튜브 모델링
scope_mount = Entity(parent=gun_holder, model='cube', scale=(0.06, 0.06, 0.12), position=(0, 0.16, -0.05), color=color.hex('#0f172a'))
scope_tube = Entity(parent=gun_holder, model='cube', scale=(0.11, 0.11, 0.38), position=(0, 0.22, -0.05), color=color.hex('#1e293b'))
scope_lens = Entity(parent=gun_holder, model='quad', scale=(0.08, 0.08), position=(0, 0.22, 0.14), color=color.hex('#00f2fe'))

# 총열
barrel = Entity(parent=gun_holder, model='cube', scale=(0.08, 0.08, 0.3), position=(0, 0.02, 0.45), color=color.hex('#0f172a'))

# 총구 섬광 (Pulse Flash)
muzzle_flash = Entity(
    parent=gun_holder,
    model='sphere',
    scale=(0.35, 0.35, 0.35),
    position=(0, 0.02, 0.65),
    color=color.cyan,
    enabled=False
)
flash_light = PointLight(parent=gun_holder, position=(0, 0.02, 0.65), color=color.cyan, intensity=0)

# --- 오버워치 스타일 UI / HUD ---
# 1. 기본 조준선 (Crosshair - 비조준 시)
crosshair_group = Entity(parent=camera.ui)
ch_top = Entity(parent=crosshair_group, model='quad', scale=(0.003, 0.015), position=(0, 0.02), color=color.lime)
ch_bot = Entity(parent=crosshair_group, model='quad', scale=(0.003, 0.015), position=(0, -0.02), color=color.lime)
ch_lft = Entity(parent=crosshair_group, model='quad', scale=(0.015, 0.003), position=(-0.02, 0), color=color.lime)
ch_rgt = Entity(parent=crosshair_group, model='quad', scale=(0.015, 0.003), position=(0.02, 0), color=color.lime)
ch_dot = Entity(parent=crosshair_group, model='quad', scale=(0.004, 0.004), color=color.lime)

# 2. 스나이퍼 정조준(ADS) 스코프 HUD 오버레이
scope_overlay = Entity(parent=camera.ui, enabled=False)

# 주변 암전 비네트 마스크
Entity(parent=scope_overlay, model='quad', scale=(0.7, 2.0), position=(-0.82, 0), color=color.black)
Entity(parent=scope_overlay, model='quad', scale=(0.7, 2.0), position=(0.82, 0), color=color.black)
Entity(parent=scope_overlay, model='quad', scale=(2.0, 0.55), position=(0, 0.72), color=color.black)
Entity(parent=scope_overlay, model='quad', scale=(2.0, 0.55), position=(0, -0.72), color=color.black)

# 스코프 조준선 & 밀닷 눈금
Entity(parent=scope_overlay, model='quad', scale=(1.6, 0.0015), color=color.hex('#ff4757'))
Entity(parent=scope_overlay, model='quad', scale=(0.0015, 1.6), color=color.hex('#ff4757'))
Entity(parent=scope_overlay, model='quad', scale=(0.006, 0.006), color=color.hex('#00f2fe')) # 정밀 조준점

for dist_x in [-0.2, -0.15, -0.1, -0.05, 0.05, 0.1, 0.15, 0.2]:
    Entity(parent=scope_overlay, model='quad', scale=(0.0015, 0.015), position=(dist_x, 0), color=color.hex('#ff4757'))
for dist_y in [-0.2, -0.15, -0.1, -0.05, 0.05, 0.1, 0.15, 0.2]:
    Entity(parent=scope_overlay, model='quad', scale=(0.015, 0.0015), position=(0, dist_y), color=color.hex('#ff4757'))

# 스코프 코너 괄호
Entity(parent=scope_overlay, model='quad', scale=(0.04, 0.003), position=(-0.35, 0.35), color=color.hex('#00f2fe'))
Entity(parent=scope_overlay, model='quad', scale=(0.003, 0.04), position=(-0.37, 0.33), color=color.hex('#00f2fe'))
Entity(parent=scope_overlay, model='quad', scale=(0.04, 0.003), position=(0.35, 0.35), color=color.hex('#00f2fe'))
Entity(parent=scope_overlay, model='quad', scale=(0.003, 0.04), position=(0.37, 0.33), color=color.hex('#00f2fe'))

Text(parent=scope_overlay, text="[ 4.0X OPTICAL SCOPE ]", position=(-0.16, 0.38), scale=1.3, color=color.hex('#00f2fe'))
Text(parent=scope_overlay, text="HEADSHOT MULTIPLIER: 2.5X", position=(-0.19, -0.38), scale=1.1, color=color.hex('#fa9c1e'))

# 3. 오버워치 히트마커 (Hit Marker)
hm1 = Entity(parent=camera.ui, model='quad', scale=(0.02, 0.003), rotation_z=45, color=color.red, enabled=False)
hm2 = Entity(parent=camera.ui, model='quad', scale=(0.02, 0.003), rotation_z=-45, color=color.red, enabled=False)

def show_hitmarker(is_kill=False, is_headshot=False):
    if is_headshot:
        c = color.hex('#f59e0b')  # 헤드샷: 황금색
    elif is_kill:
        c = color.red
    else:
        c = color.orange
    hm1.color = c
    hm2.color = c
    hm1.enabled = True
    hm2.enabled = True
    invoke(setattr, hm1, 'enabled', False, delay=0.1)
    invoke(setattr, hm2, 'enabled', False, delay=0.1)

# 4. 체력 & 탄약 & 궁극기 HUD
hp_bg = Entity(parent=camera.ui, model='quad', scale=(0.32, 0.04), position=(-0.65, -0.4), color=color.rgba(0, 0, 0, 0.6))
hp_bar = Entity(parent=camera.ui, model='quad', scale=(0.3, 0.03), position=(-0.65, -0.4), color=color.white)
hp_text = Text(text=f"{player_hp} / {max_player_hp}", position=(-0.8, -0.34), scale=1.4, color=color.white)

max_ammo = 25
ammo = 25
is_reloading = False
is_scoped = False

ammo_text = Text(text=f"{ammo}", position=(0.68, -0.35), scale=3.0, color=color.azure)
ammo_sub = Text(text=f"/ {max_ammo}", position=(0.78, -0.37), scale=1.3, color=color.light_gray)

ult_charge = 0
ult_active = False
ult_timer = 0.0
ult_bg = Entity(parent=camera.ui, model='quad', scale=(0.14, 0.06), position=(0, -0.38), color=color.rgba(0, 0, 0, 0.7))
ult_text = Text(text="0%", position=(-0.03, -0.36), scale=1.5, color=color.azure)
ult_guide = Text(text="[Q] 전술 조준경", position=(-0.07, -0.42), scale=1.0, color=color.orange, enabled=False)

# 전술 조준경 테두리 HUD & 락온 박스
visor_border_top = Entity(parent=camera.ui, model='quad', scale=(1.8, 0.008), position=(0, 0.48), color=color.orange, enabled=False)
visor_border_bot = Entity(parent=camera.ui, model='quad', scale=(1.8, 0.008), position=(0, -0.48), color=color.orange, enabled=False)
visor_border_lft = Entity(parent=camera.ui, model='quad', scale=(0.008, 0.96), position=(-0.88, 0), color=color.orange, enabled=False)
visor_border_rgt = Entity(parent=camera.ui, model='quad', scale=(0.008, 0.96), position=(0.88, 0), color=color.orange, enabled=False)
visor_title = Text(text="⚡ TACTICAL VISOR ACTIVE ⚡", position=(-0.25, 0.38), scale=1.8, color=color.orange, enabled=False)
lock_on_marker = Entity(model='wireframe_cube', scale=(2.2, 3.2, 2.2), color=color.red, enabled=False)

# 처치 및 헤드샷 피드 텍스트
kill_feed = Text(text="", position=(-0.22, 0.25), scale=1.7, color=color.red, enabled=False)

def announce_kill(bot_name, is_headshot=False):
    if is_headshot:
        kill_feed.text = f"🎯 CRITICAL HEADSHOT! {bot_name} (+150)"
        kill_feed.color = color.hex('#f59e0b')
    else:
        kill_feed.text = f"ELIMINATED {bot_name} (+100)"
        kill_feed.color = color.red
    kill_feed.enabled = True
    invoke(setattr, kill_feed, 'enabled', False, delay=1.3)

score = 0
score_text = Text(text="ELIMINATIONS: 0", position=(-0.85, 0.45), scale=1.3, color=color.white)


# --- 사람 형태의 휴머노이드 훈련 봇 (Humanoid Combat Bot) ---
bots = []

class HumanoidBot(Entity):
    def __init__(self, position):
        super().__init__(position=position)
        self.max_hp = 150
        self.hp = 150

        # 1. 머리 (헤드샷 판정용 전용 콜라이더 장착!)
        self.head = Entity(
            parent=self,
            model='sphere',
            scale=(0.85, 0.85, 0.85),
            position=(0, 2.7, 0),
            color=color.hex('#f1f3f5'),
            collider='box'
        )
        self.visor = Entity(parent=self.head, model='cube', scale=(0.7, 0.15, 0.3), position=(0, 0, 0.4), color=color.hex('#00f2fe'))

        # 2. 상체 (아머 플레이트 & 방탄 조끼)
        self.chest = Entity(
            parent=self,
            model='cube',
            scale=(1.4, 1.2, 0.8),
            position=(0, 1.8, 0),
            color=color.hex('#e03131'),
            collider='box'
        )
        self.vest = Entity(parent=self.chest, model='cube', scale=(1.05, 0.75, 1.05), position=(0, 0.05, 0), color=color.hex('#1e293b'))

        # 3. 허리 & 골반
        self.waist = Entity(parent=self, model='cube', scale=(0.9, 0.45, 0.65), position=(0, 1.0, 0), color=color.hex('#334155'))

        # 4. 양팔 (어깨 + 팔)
        self.arm_l = Entity(parent=self, model='cube', scale=(0.35, 1.2, 0.35), position=(-1.0, 1.6, 0), color=color.hex('#e03131'))
        self.arm_r = Entity(parent=self, model='cube', scale=(0.35, 1.2, 0.35), position=(1.0, 1.6, 0), color=color.hex('#e03131'))

        # 5. 양다리 (전투 스탠스)
        self.leg_l = Entity(parent=self, model='cube', scale=(0.4, 1.3, 0.4), position=(-0.45, 0.3, 0), color=color.hex('#1e293b'))
        self.leg_r = Entity(parent=self, model='cube', scale=(0.4, 1.3, 0.4), position=(0.45, 0.3, 0), color=color.hex('#1e293b'))

        # 전체 바디 콜라이더 (몸체 피격용)
        self.collider = BoxCollider(self, size=(1.8, 3.2, 1.0), center=(0, 1.6, 0))

        # 머리 위 체력바
        self.hp_bg = Entity(parent=self, model='quad', scale=(1.5, 0.15), position=(0, 3.5, 0), color=color.hex('#000000'), billboard=True)
        self.hp_fg = Entity(parent=self, model='quad', scale=(1.5, 0.13), position=(0, 3.5, -0.01), color=color.hex('#ff4757'), billboard=True)

        self.base_y = position[1]
        self.time_offset = random.random() * 5

    def update(self):
        # 상하 숨쉬기/가벼운 부유 애니메이션
        self.y = self.base_y + math.sin(time.time() * 2 + self.time_offset) * 0.08
        self.look_at_2d(player.position, 'y')

    def take_hit(self, damage, is_headshot=False):
        self.hp -= damage

        # 피격 효과: 헤드샷 시 황금색 섬광, 일반 피격 시 화이트
        flash_col = color.hex('#f59e0b') if is_headshot else color.white
        self.head.color = flash_col
        self.chest.color = flash_col
        invoke(self.restore_color, delay=0.08)

        # 체력바 갱신
        ratio = max(0.0, self.hp / self.max_hp)
        self.hp_fg.scale_x = 1.5 * ratio
        self.hp_fg.x = -1.5 * (1 - ratio) / 2

        # 궁극기 충전 (+12% for headshot, +8% normal)
        add_ult_charge(12 if is_headshot else 8)

        if self.hp <= 0:
            show_hitmarker(is_kill=True, is_headshot=is_headshot)
            announce_kill("TRAINING BOT", is_headshot=is_headshot)
            destroy_bot(self)
        else:
            show_hitmarker(is_kill=False, is_headshot=is_headshot)

    def restore_color(self):
        if self and self.enabled:
            self.head.color = color.hex('#f1f3f5')
            self.chest.color = color.hex('#e03131')

def spawn_bot(x=None, z=None):
    if x is None:
        x = random.choice([-30, -15, 0, 15, 30]) + random.uniform(-3, 3)
    if z is None:
        z = random.uniform(15, 48)
    bot = HumanoidBot(position=(x, 0, z))
    bots.append(bot)

def destroy_bot(bot):
    for _ in range(10):
        debris = Entity(
            model='cube',
            scale=0.22,
            position=bot.position + Vec3(random.uniform(-0.5, 0.5), random.uniform(0.5, 2.5), random.uniform(-0.5, 0.5)),
            color=random.choice([color.hex('#e03131'), color.hex('#1e293b'), color.hex('#00f2fe'), color.white])
        )
        debris.animate_position(debris.position + Vec3(random.uniform(-3, 3), random.uniform(1, 4), random.uniform(-3, 3)), duration=0.45)
        debris.animate_scale(0.01, duration=0.45)
        destroy(debris, delay=0.45)

    if bot in bots:
        bots.remove(bot)
    destroy(bot)

    global score
    score += 1
    score_text.text = f"ELIMINATIONS: {score}"
    invoke(spawn_bot, delay=2.5)

# 초기 훈련 봇 6대 배치
spawn_bot(-25, 20)
spawn_bot(-12, 35)
spawn_bot(0, 25)
spawn_bot(12, 38)
spawn_bot(25, 18)
spawn_bot(0, 48)


# --- 궁극기 충전 ---
def add_ult_charge(amount):
    global ult_charge
    if ult_active:
        return
    ult_charge = min(100, ult_charge + amount)
    ult_text.text = f"{ult_charge}%"
    if ult_charge >= 100:
        ult_text.text = "READY"
        ult_text.color = color.orange
        ult_guide.enabled = True


# --- 레이저 탄환 궤적 (Pulse Tracer) ---
def create_tracer(start, end, is_sniper=False):
    dist = (end - start).length()
    thickness = 0.08 if is_sniper else 0.04
    tracer = Entity(
        model='cube',
        scale=(thickness, thickness, dist),
        position=(start + end) / 2,
        color=color.hex('#00f2fe') if not is_sniper else color.hex('#38bdf8')
    )
    tracer.look_at(end)
    tracer.animate_scale((0.005, 0.005, dist), duration=0.12 if is_sniper else 0.09)
    destroy(tracer, delay=0.12 if is_sniper else 0.09)


# --- 사격 시스템 & 스나이퍼 발사 모션 ---
fire_rate = 0.11
last_shot_time = 0

def shoot():
    global ammo, last_shot_time, is_reloading
    if is_reloading:
        return

    current_time = time.time()
    rate = 0.28 if is_scoped else (0.07 if ult_active else fire_rate)
    if current_time - last_shot_time < rate:
        return

    if ammo <= 0:
        reload()
        return

    last_shot_time = current_time
    ammo -= 1
    ammo_text.text = f"{ammo}"

    # 반동 모션 (스나이퍼 줌 상태일 때는 화면 진동, 지향사격 시 총기 펀치력 있는 반동)
    if is_scoped:
        camera.rotation_x -= 1.8  # 총구 튀어오름
        invoke(setattr, camera, 'rotation_x', camera.rotation_x + 1.8, delay=0.08)
    else:
        gun_holder.position = Vec3(0.38, -0.27, 0.50)
        gun_holder.rotation = Vec3(-8, 3, 3)
        gun_holder.animate_position(Vec3(0.38, -0.32, 0.65), duration=rate * 0.8, curve=curve.out_quad)
        gun_holder.animate_rotation(Vec3(0, 0, 0), duration=rate * 0.8, curve=curve.out_quad)

    # 총구 화염 및 플래시 조명
    muzzle_flash.enabled = True
    flash_light.intensity = 3.5 if is_scoped else 2.5
    invoke(setattr, muzzle_flash, 'enabled', False, delay=0.04)
    invoke(setattr, flash_light, 'intensity', 0, delay=0.04)

    # 사격 레이캐스트 판정
    shoot_origin = camera.world_position
    shoot_dir = camera.forward

    if ult_active and bots:
        # 궁극기 발동 시 가장 가까운 봇 자동 락온
        target_bot = min(bots, key=lambda b: (b.position - player.position).length())
        shoot_dir = (target_bot.position + Vec3(0, 2.0, 0) - shoot_origin).normalized()

    muzzle_world_pos = gun_holder.world_position + gun_holder.forward * 0.6
    hit_info = raycast(shoot_origin, shoot_dir, distance=150, ignore=(player, gun_holder))

    if hit_info.hit:
        end_pos = hit_info.point
        create_tracer(muzzle_world_pos, end_pos, is_sniper=is_scoped)

        # 착탄 스파크
        spark = Entity(model='sphere', scale=0.25 if is_scoped else 0.15, position=end_pos, color=color.hex('#00f2fe'))
        spark.animate_scale(0.01, duration=0.1)
        destroy(spark, delay=0.1)

        # 봇 및 헤드샷 피격 판정
        hit_e = hit_info.entity
        found_bot = None
        is_headshot = False

        curr = hit_e
        while curr:
            if hasattr(curr, 'head') and (hit_e == curr.head or hit_e == curr.visor):
                is_headshot = True
            if isinstance(curr, HumanoidBot):
                found_bot = curr
                break
            curr = curr.parent

        if found_bot:
            # 데미지 계산 (스나이퍼 줌 90, 일반 35, 헤드샷 시 2.5배 치명타!)
            base_dmg = 90 if is_scoped else (45 if ult_active else 35)
            final_dmg = int(base_dmg * 2.5) if is_headshot else base_dmg
            found_bot.take_hit(final_dmg, is_headshot=is_headshot)
    else:
        end_pos = shoot_origin + shoot_dir * 100
        create_tracer(muzzle_world_pos, end_pos, is_sniper=is_scoped)


# --- 찰진 5단계 택티컬 재장전 (Tactical Reload Animation) ---
def reload():
    global is_reloading, ammo, is_scoped
    if is_reloading or ammo == max_ammo:
        return

    # 조준 중이면 스나이퍼 모드 해제
    if is_scoped:
        set_scope(False)

    is_reloading = True
    ammo_text.text = "--"

    # 1단계 (0.0s): 총기를 비스듬히 눕히며 왼손이 탄창으로 이동
    gun_holder.animate_rotation(Vec3(22, -25, 25), duration=0.3, curve=curve.out_quad)
    gun_holder.animate_position(Vec3(0.32, -0.38, 0.55), duration=0.3, curve=curve.out_quad)
    left_hand.animate_position((0, -0.15, 0.1), duration=0.25)

    # 2단계 (0.3s): 사용한 탄창 배출 (아래로 툭 분리)
    def drop_mag():
        magazine.animate_position((0, -0.65, 0.08), duration=0.25, curve=curve.in_quad)
        magazine.color = color.hex('#475569')

    invoke(drop_mag, delay=0.3)

    # 3단계 (0.6s): 새 완충 에너지 탄창을 아래에서 '착!' 결합
    def insert_new_mag():
        magazine.position = (0, -0.65, 0.08)
        magazine.color = color.hex('#00f2fe')
        magazine.animate_position((0, -0.15, 0.08), duration=0.25, curve=curve.out_quad)
        left_hand.animate_position((0, -0.12, 0.08), duration=0.25)

    invoke(insert_new_mag, delay=0.6)

    # 4단계 (0.9s): 왼손이 상단 노리쇠(Bolt)를 뒤로 '철-컥!' 당겼다 놓음
    def cock_bolt():
        left_hand.animate_position((0, 0.12, -0.12), duration=0.15)
        invoke(lambda: left_hand.animate_position((-0.08, -0.07, 0.25), duration=0.18), delay=0.15)

    invoke(cock_bolt, delay=0.9)

    # 5단계 (1.25s): 원래 파지 자세로 복귀 및 탄약 완충
    def finish_reload():
        global ammo, is_reloading
        ammo = max_ammo
        ammo_text.text = f"{ammo}"
        gun_holder.animate_rotation(Vec3(0, 0, 0), duration=0.2, curve=curve.out_quad)
        gun_holder.animate_position(Vec3(0.38, -0.32, 0.65), duration=0.2, curve=curve.out_quad)
        is_reloading = False

    invoke(finish_reload, delay=1.25)


# --- 스나이퍼 조준(ADS) 토글/설정 ---
def set_scope(scoped: bool):
    global is_scoped
    if is_reloading and scoped:
        return
    is_scoped = scoped
    if is_scoped:
        scope_overlay.enabled = True
        crosshair_group.enabled = False
        player.mouse_sensitivity = Vec2(16, 16) # 정밀 조준용 감도
    else:
        scope_overlay.enabled = False
        crosshair_group.enabled = True
        player.mouse_sensitivity = Vec2(40, 40) # 일반 감도 복구


# --- 궁극기 발동 (Q: 전술 조준경) ---
def activate_ultimate():
    global ult_active, ult_timer, ult_charge
    if ult_charge < 100 or ult_active:
        return

    ult_charge = 0
    ult_active = True
    ult_timer = 6.0
    ult_text.text = "ACTIVE"
    ult_text.color = color.red
    ult_guide.enabled = False

    visor_border_top.enabled = True
    visor_border_bot.enabled = True
    visor_border_lft.enabled = True
    visor_border_rgt.enabled = True
    visor_title.enabled = True


# --- 메인 프레임 루프 (물리, 호흡, 보빙, 스코프 줌) ---
prev_mouse_x = 0
prev_mouse_y = 0
walk_cycle = 0

def update():
    global prev_mouse_x, prev_mouse_y, walk_cycle, ult_active, ult_timer

    dt = time.dt

    # 카메라 롤(Z축)과 엉뚱한 로컬 Yaw(Y축) 회전 방지
    camera.rotation_z = 0
    camera.rotation_y = 0

    # 1. 우클릭 시 스나이퍼 줌 (ADS) 부드러운 전환
    wants_scope = held_keys['right mouse'] and not is_reloading
    if wants_scope != is_scoped:
        set_scope(wants_scope)

    target_fov = 14 if is_scoped else 40
    camera.fov = lerp(camera.fov, target_fov, dt * 15)

    # 2. 궁극기 지속 시간 및 락온 박스
    if ult_active:
        ult_timer -= dt
        ult_text.text = f"{ult_timer:.1f}s"

        if bots:
            closest_bot = min(bots, key=lambda b: (b.position - player.position).length())
            lock_on_marker.position = closest_bot.position + Vec3(0, 1.8, 0)
            lock_on_marker.enabled = True
        else:
            lock_on_marker.enabled = False

        if ult_timer <= 0:
            ult_active = False
            visor_border_top.enabled = False
            visor_border_bot.enabled = False
            visor_border_lft.enabled = False
            visor_border_rgt.enabled = False
            visor_title.enabled = False
            lock_on_marker.enabled = False
            ult_text.text = "0%"
            ult_text.color = color.azure
    else:
        lock_on_marker.enabled = False

    # 3. 사격 처리 (좌클릭 유지 시 연사, 스나이퍼 모드 시 단발)
    if held_keys['left mouse']:
        shoot()

    # 4. 웨폰 스웨이 & 호흡(Breathing) & 걷기 보빙(Bobbing)
    mouse_dx = mouse.velocity[0]
    mouse_dy = mouse.velocity[1]
    target_rot_y = -mouse_dx * 20
    target_rot_x = mouse_dy * 20

    if not is_reloading:
        gun_holder.rotation_y = lerp(gun_holder.rotation_y, target_rot_y, dt * 10)
        gun_holder.rotation_x = lerp(gun_holder.rotation_x, target_rot_x, dt * 10)

    # 스나이퍼 줌 중일 때는 총기가 시야 아래로 정돈
    target_gun_y = -0.75 if is_scoped else -0.32
    target_gun_x = 0.38

    # 이동 보빙 및 호흡 모션
    is_moving = held_keys['w'] or held_keys['s'] or held_keys['a'] or held_keys['d']
    if not is_reloading:
        if is_moving and player.grounded and not is_scoped:
            walk_cycle += dt * 12
            bob_x = math.sin(walk_cycle) * 0.015
            bob_y = math.cos(walk_cycle * 2) * 0.012
            gun_holder.x = target_gun_x + bob_x
            gun_holder.y = target_gun_y + bob_y
        else:
            # 숨쉬기(Idle Breathing) 모션
            breath = math.sin(time.time() * 2.5) * 0.004
            gun_holder.x = lerp(gun_holder.x, target_gun_x, dt * 8)
            gun_holder.y = lerp(gun_holder.y, target_gun_y + breath, dt * 8)

    # 5. 슈퍼 점프 패드 충돌
    dist_to_pad = (player.position - jump_pad.position).length()
    if dist_to_pad < 2.5 and player.y < 0.8:
        player.jump_height = 8.0
        player.jump()
        player.jump_height = 2.0


def input(key):
    if key == 'left mouse down':
        shoot()
    elif key == 'r':
        reload()
    elif key == 'q':
        activate_ultimate()
    elif key == 'escape':
        mouse.locked = not mouse.locked
        player.enabled = mouse.locked


if __name__ == '__main__':
    print("오버워치 스타일 3D 훈련장 (스나이퍼 & 택티컬 모션 에디션)을 실행합니다...")
    app.run()
