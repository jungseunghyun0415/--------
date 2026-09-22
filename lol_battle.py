"""
리그 오브 레전드(LoL) 미니 텍스트 배틀 게임
소환사의 협곡 1:1 대전 시뮬레이터
"""

import random
import time
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Skill:
    name: str
    key: str  # Q, W, E, R
    mana_cost: int
    cooldown: int
    current_cd: int = 0
    desc: str = ""


class Champion:
    def __init__(
        self,
        name: str,
        title: str,
        max_hp: int,
        max_mp: int,
        ad: int,
        ap: int,
        armor: int,
        mr: int,
    ):
        self.name = name
        self.title = title
        self.max_hp = max_hp
        self.hp = max_hp
        self.max_mp = max_mp
        self.mp = max_mp
        self.ad = ad
        self.ap = ap
        self.armor = armor
        self.mr = mr
        self.shield = 0

        # 상태 이상 (턴 수)
        self.stunned = 0
        self.silenced = 0
        self.damage_reduction = 0.0  # 피해 감소율

        self.skills: List[Skill] = []

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, raw_damage: int, damage_type: str = "physical") -> int:
        """방어력/마법저항력 및 보호막을 적용하여 피해를 입힘"""
        # 피해 감소 버프 계산
        raw_damage = int(raw_damage * (1.0 - self.damage_reduction))

        if damage_type == "physical":
            reduced = raw_damage * (100 / (100 + self.armor))
        elif damage_type == "magic":
            reduced = raw_damage * (100 / (100 + self.mr))
        else:  # true damage (고정 피해)
            reduced = raw_damage

        final_dmg = max(1, int(reduced))

        # 보호막 우선 차감
        if self.shield > 0:
            if self.shield >= final_dmg:
                self.shield -= final_dmg
                return 0
            else:
                final_dmg -= self.shield
                self.shield = 0

        self.hp = max(0, self.hp - final_dmg)
        return final_dmg

    def update_turn(self):
        """턴 시작 시 쿨다운 감소, 상태이상 감소, 마나 자연 회복"""
        # 쿨다운 감소
        for skill in self.skills:
            if skill.current_cd > 0:
                skill.current_cd -= 1

        # 상태이상 감소
        if self.stunned > 0:
            self.stunned -= 1
        if self.silenced > 0:
            self.silenced -= 1
        self.damage_reduction = 0.0

        # 자연 회복
        self.mp = min(self.max_mp, self.mp + 10)

    def get_hp_bar(self, length: int = 20) -> str:
        ratio = max(0.0, min(1.0, self.hp / self.max_hp))
        filled = int(ratio * length)
        bar = "█" * filled + "░" * (length - filled)
        shield_txt = f" (+{self.shield}🛡️)" if self.shield > 0 else ""
        return f"[{bar}] {self.hp}/{self.max_hp}{shield_txt}"

    def get_mp_bar(self, length: int = 15) -> str:
        ratio = max(0.0, min(1.0, self.mp / self.max_mp)) if self.max_mp > 0 else 0
        filled = int(ratio * length)
        bar = "■" * filled + "□" * (length - filled)
        return f"[{bar}] {self.mp}/{self.max_mp}"


# --- 챔피언 세부 클래스 ---
class Garen(Champion):
    def __init__(self):
        super().__init__(
            name="가렌",
            title="데마시아의 힘",
            max_hp=690,
            max_mp=100,  # 가렌은 노코스트지만 편의상 100 표기
            ad=66,
            ap=0,
            armor=36,
            mr=32,
        )
        self.skills = [
            Skill("결정타 (Q)", "Q", 0, 3, 0, "강력한 공격과 함께 상대를 1턴간 침묵시킵니다."),
            Skill("용기 (W)", "W", 0, 4, 0, "보호막을 얻고 1턴간 받는 피해를 30% 감소시킵니다."),
            Skill("심판 (E)", "E", 0, 3, 0, "검을 회전시켜 적에게 방어력 무시 연타를 가합니다."),
            Skill("데마시아의 정의 (R)", "R", 0, 5, 0, "적 잃은 체력에 비례한 고정 피해 궁극기!"),
        ]

    def use_skill(self, skill_key: str, target: Champion) -> str:
        if skill_key == "Q":
            dmg = target.take_damage(int(self.ad * 1.5 + 40), "physical")
            target.silenced = 1
            return f"가렌이 [결정타(Q)]를 내려찍어 {dmg}의 물리 피해를 주고 침묵시켰습니다!"
        elif skill_key == "W":
            self.shield += 120
            self.damage_reduction = 0.3
            return f"가렌이 [용기(W)]를 발동하여 120의 보호막을 얻고 받는 피해가 30% 감소합니다!"
        elif skill_key == "E":
            total_dmg = 0
            for _ in range(4):
                total_dmg += target.take_damage(int(self.ad * 0.45 + 15), "physical")
            return f"가렌이 빙글빙글 돌며 [심판(E)]으로 총 {total_dmg}의 물리 피해를 입혔습니다!"
        elif skill_key == "R":
            missing_hp = target.max_hp - target.hp
            raw_dmg = 150 + int(missing_hp * 0.3)
            dmg = target.take_damage(raw_dmg, "true")
            return f"⚡ 데마시아아아앗!! [데마시아의 정의(R)]로 {dmg}의 고정 피해를 폭발시켰습니다!"
        return ""


class Ahri(Champion):
    def __init__(self):
        super().__init__(
            name="아리",
            title="구미호",
            max_hp=570,
            max_mp=418,
            ad=53,
            ap=80,
            armor=21,
            mr=30,
        )
        self.skills = [
            Skill("현혹의 구슬 (Q)", "Q", 60, 2, 0, "구슬을 던져 마법 피해와 돌아오는 고정 피해를 입힙니다."),
            Skill("여우불 (W)", "W", 30, 2, 0, "여우불 3개를 소환해 집중 마법 타격을 가합니다."),
            Skill("매혹 (E)", "E", 50, 4, 0, "적을 매혹해 1턴간 행동불능(스턴)으로 만듭니다."),
            Skill("혼령 질주 (R)", "R", 100, 5, 0, "3회 연속 질주하며 치명적인 마법 폭딜을 쏟아붓습니다."),
        ]

    def use_skill(self, skill_key: str, target: Champion) -> str:
        if skill_key == "Q":
            dmg1 = target.take_damage(int(self.ap * 0.7 + 40), "magic")
            dmg2 = target.take_damage(int(self.ap * 0.5 + 30), "true")
            return f"아리가 [현혹의 구슬(Q)]을 날려 마법 피해({dmg1})와 고정 피해({dmg2})를 입혔습니다!"
        elif skill_key == "W":
            dmg = target.take_damage(int(self.ap * 0.8 + 50), "magic")
            return f"아리의 [여우불(W)]이 적을 맹렬히 추적하여 {dmg}의 마법 피해를 입혔습니다!"
        elif skill_key == "E":
            dmg = target.take_damage(int(self.ap * 0.4 + 40), "magic")
            target.stunned = 1
            return f"💖 하트 발사! [매혹(E)]에 걸려든 상대가 홀려 1턴간 행동불능 상태가 되며 {dmg}의 피해를 입었습니다!"
        elif skill_key == "R":
            total_dmg = 0
            for _ in range(3):
                total_dmg += target.take_damage(int(self.ap * 0.6 + 60), "magic")
            return f"✨ 아리가 [혼령 질주(R)]로 전장을 가로지르며 총 {total_dmg}의 강력한 마법 피해를 퍼부었습니다!"
        return ""


class Yasuo(Champion):
    def __init__(self):
        super().__init__(
            name="야스오",
            title="용서받지 못한 자",
            max_hp=590,
            max_mp=100,  # 기류 게이지
            ad=60,
            ap=0,
            armor=30,
            mr=32,
        )
        self.tornado_ready = False
        self.skills = [
            Skill("강철 폭풍 (Q)", "Q", 0, 1, 0, "전방을 찔러 검기를 모으며 2회 적중 시 회오리바람을 생성합니다."),
            Skill("바람의 장막 (W)", "W", 0, 4, 0, "투사체를 막는 장막을 펼쳐 보호막을 획득합니다."),
            Skill("질풍검 (E)", "E", 0, 1, 0, "적 사이를 파고들며 재빠른 마법 공격을 펼칩니다."),
            Skill("최후의 숨결 (R)", "R", 0, 5, 0, "공중에 뜬 적에게 순간이동하여 난타합니다. (회오리 필요)"),
        ]

    def use_skill(self, skill_key: str, target: Champion) -> str:
        if skill_key == "Q":
            crit = 2 if random.random() < 0.4 else 1  # 40% 치명타
            crit_txt = " (치명타!)" if crit == 2 else ""
            if self.tornado_ready:
                dmg = target.take_damage(int((self.ad * 1.6 + 30) * crit), "physical")
                target.stunned = 1
                self.tornado_ready = False
                return f"하세기!! 🌪️ 회오리바람 [강철 폭풍(Q)]{crit_txt}으로 {dmg} 피해를 입히고 에어본(스턴)을 걸었습니다!"
            else:
                dmg = target.take_damage(int((self.ad * 1.1 + 20) * crit), "physical")
                self.tornado_ready = True
                return f"돈!(Q){crit_txt} {dmg} 피해를 입혔습니다. [회오리바람 장전 완료!]"
        elif skill_key == "W":
            self.shield += 130
            return f"야스오가 [바람의 장막(W)]을 소환해 130의 보호막을 생성했습니다!"
        elif skill_key == "E":
            dmg = target.take_damage(int(self.ad * 0.7 + 40), "magic")
            return f"야스오가 바람처럼 파고들며 [질풍검(E)]으로 {dmg} 마법 피해를 입혔습니다!"
        elif skill_key == "R":
            dmg = target.take_damage(int(self.ad * 2.5 + 100), "physical")
            return f"소리에게돈!! ⚔️ [최후의 숨결(R)]로 공중에서 무자비한 난도질을 가해 {dmg}의 치명상을 입혔습니다!"
        return ""


def get_champion_by_choice(choice: int) -> Champion:
    if choice == 1:
        return Garen()
    elif choice == 2:
        return Ahri()
    else:
        return Yasuo()


def print_status(player: Champion, enemy: Champion):
    print("\n" + "=" * 55)
    print(f"🎮 [소환사] {player.name} ({player.title})")
    print(f"HP : {player.get_hp_bar()}")
    print(f"MP : {player.get_mp_bar()}")
    status_player = []
    if player.stunned > 0:
        status_player.append("💫기절")
    if player.silenced > 0:
        status_player.append("🔇침묵")
    if status_player:
        print(f"상태: {', '.join(status_player)}")

    print("-" * 55)
    print(f"👾 [상대 AI] {enemy.name} ({enemy.title})")
    print(f"HP : {enemy.get_hp_bar()}")
    print(f"MP : {enemy.get_mp_bar()}")
    status_enemy = []
    if enemy.stunned > 0:
        status_enemy.append("💫기절")
    if enemy.silenced > 0:
        status_enemy.append("🔇침묵")
    if status_enemy:
        print(f"상태: {', '.join(status_enemy)}")
    print("=" * 55)


def player_turn(player: Champion, enemy: Champion):
    player.update_turn()
    print_status(player, enemy)

    if player.stunned > 0:
        print(f"\n💫 {player.name}이(가) 기절하여 이번 턴에는 행동할 수 없습니다!")
        return

    while True:
        print("\n[행동 선택]")
        print("0. 기본 공격 (평타)")
        for idx, skill in enumerate(player.skills, 1):
            cd_info = f"[쿨다운: {skill.current_cd}턴]" if skill.current_cd > 0 else "[사용 가능]"
            cost_info = f"MP {skill.mana_cost}" if skill.mana_cost > 0 else "노코스트"
            print(f"{idx}. {skill.name} ({cost_info}) - {cd_info}")
            print(f"   └ {skill.desc}")

        sel = input("\n원하는 행동 번호를 입력하세요: ").strip()

        if sel == "0":
            # 기본 공격
            crit = 1.5 if random.random() < 0.2 else 1.0
            raw_dmg = int(player.ad * crit)
            crit_txt = " (치명타 발동!)" if crit > 1.0 else ""
            dmg = enemy.take_damage(raw_dmg, "physical")
            print(f"\n⚔️ {player.name}의 기본 공격!{crit_txt} {enemy.name}에게 {dmg}의 피해를 입혔습니다.")
            break

        elif sel in ["1", "2", "3", "4"]:
            skill_idx = int(sel) - 1
            skill = player.skills[skill_idx]

            if player.silenced > 0:
                print("🔇 침묵 상태여서 스킬을 사용할 수 없습니다! 기본 공격을 사용하세요.")
                continue
            if skill.current_cd > 0:
                print(f"⚠️ 아직 쿨다운 중입니다! ({skill.current_cd}턴 남음)")
                continue
            if player.mp < skill.mana_cost:
                print(f"⚠️ 마나가 부족합니다! (필요 MP: {skill.mana_cost}, 현재 MP: {player.mp})")
                continue

            # 야스오 궁극기 조건
            if isinstance(player, Yasuo) and skill.key == "R":
                if enemy.stunned == 0:
                    print("⚠️ 상대가 에어본(기절) 상태일 때만 궁극기(최후의 숨결)를 사용할 수 있습니다! (Q 회오리로 띄우세요)")
                    continue

            # 스킬 발동
            player.mp -= skill.mana_cost
            skill.current_cd = skill.cooldown
            msg = player.use_skill(skill.key, enemy)
            print(f"\n✨ {msg}")
            break
        else:
            print("올바른 번호를 입력해주세요.")


def ai_turn(enemy: Champion, player: Champion):
    enemy.update_turn()
    time.sleep(0.8)

    if enemy.stunned > 0:
        print(f"\n💫 [상대] {enemy.name}이(가) 행동불능(스턴) 상태입니다!")
        return

    # AI 스킬 사용 판단
    available_skills = []
    if enemy.silenced == 0:
        for s in enemy.skills:
            if s.current_cd == 0 and enemy.mp >= s.mana_cost:
                # 야스오 궁극기 조건 체크
                if isinstance(enemy, Yasuo) and s.key == "R":
                    if player.stunned == 0:
                        continue
                available_skills.append(s)

    # R 궁극기가 가능하면 높은 확률로 시전
    ult = [s for s in available_skills if s.key == "R"]
    if ult and random.random() < 0.8:
        chosen_skill = ult[0]
    elif available_skills and random.random() < 0.65:
        chosen_skill = random.choice(available_skills)
    else:
        chosen_skill = None

    if chosen_skill:
        enemy.mp -= chosen_skill.mana_cost
        chosen_skill.current_cd = chosen_skill.cooldown
        msg = enemy.use_skill(chosen_skill.key, player)
        print(f"\n👾 [상대 AI] {enemy.name}이(가) 스킬을 사용했습니다!")
        print(f"   {msg}")
    else:
        crit = 1.5 if random.random() < 0.15 else 1.0
        dmg = player.take_damage(int(enemy.ad * crit), "physical")
        crit_txt = " (치명타!)" if crit > 1.0 else ""
        print(f"\n👾 [상대 AI] {enemy.name}의 기본 공격!{crit_txt} {player.name}에게 {dmg}의 피해를 입혔습니다.")


def start_game():
    print("""
    ========================================================
       ⚔️  LEAGUE OF LEGENDS - 소환사의 협곡 1:1 대전  ⚔️
    ========================================================
    """)
    print("플레이할 챔피언을 선택하세요:")
    print("1. 가렌 (데마시아의 힘) - 튼튼한 체력, 침묵 및 잃은 체력 비례 궁극기")
    print("2. 아리 (구미호) - 강력한 AP 마법 딜링, 매혹(스턴) 군중 제어기")
    print("3. 야스오 (용서받지 못한 자) - 치명타, 회오리바람 에어본 및 공중 궁극기")

    while True:
        try:
            choice = int(input("\n챔피언 번호 선택 (1~3): ").strip())
            if choice in [1, 2, 3]:
                break
            print("1, 2, 3 중 하나를 골라주세요.")
        except ValueError:
            print("숫자를 입력해주세요.")

    player = get_champion_by_choice(choice)

    # 상대 AI 챔피언 자동 선택 (자신과 다른 챔피언 선호)
    enemy_pool = [1, 2, 3]
    enemy_pool.remove(choice)
    enemy_choice = random.choice(enemy_pool)
    enemy = get_champion_by_choice(enemy_choice)

    print(f"\n🔔 매칭 완료! [{player.name}] vs [{enemy.name}]")
    print("소환사의 협곡에 오신 것을 환영합니다. 전투를 시작합니다!\n")
    time.sleep(1)

    turn_count = 1
    while player.is_alive() and enemy.is_alive():
        print(f"\n━━━━━━━━━━━━━━━ [ ROUND {turn_count} ] ━━━━━━━━━━━━━━━")
        # 플레이어 턴
        player_turn(player, enemy)
        if not enemy.is_alive():
            break

        # AI 턴
        ai_turn(enemy, player)
        if not player.is_alive():
            break

        turn_count += 1
        time.sleep(0.5)

    print("\n" + "=" * 55)
    if player.is_alive():
        print("🏆 승 리 (VICTORY) 🏆")
        print(f"적 챔피언 [{enemy.name}]을(를) 처치했습니다! 소환사님의 완벽한 피지컬!")
    else:
        print("💀 패 배 (DEFEAT) 💀")
        print(f"[{enemy.name}]에게 쓰러졌습니다... 다음 기회에 복수하세요!")
    print("=" * 55)


if __name__ == "__main__":
    start_game()

