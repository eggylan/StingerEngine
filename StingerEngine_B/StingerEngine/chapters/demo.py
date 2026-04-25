# -*- coding: utf-8 -*-

script_data = [
    # ---------------- 变量初始化 ----------------
    {"type": "var", "variable": "alex_affection", "operation": "set", "value": 0},
    {"type": "var", "variable": "has_pickaxe", "operation": "set", "value": False},

    # ---------------- 场景一：屋子 ----------------
    {"type": "bg", "image": "textures/modTextures/demo/bg_house_inside"},
    {"type": "music", "file": "demo.bgm.morning_village", "action": "play"},
    {"type": "fade_in", "duration": 1.5},
    
    {"type": "wait", "duration": 0.5},
    {"type": "sfx", "file": "demo.sfx.door_knock", "loop": False},
    {"type": "text", "speaker": "爱丽克丝", "content": "史蒂夫！快醒醒！太阳都升到头顶了！"},
    {"type": "text", "speaker": "史蒂夫", "content": "唔……苦力怕都还没下班呢，再让我睡五分钟……"},
    
    {"type": "sfx", "file": "demo.sfx.door_open", "loop": False},
    {"type": "character_enter", "id": "alex", "image": "char_alex_angry", "position": "center", "fade_in": 0.3},
    {"type": "character_play_anim", "id": "alex", "animdata": {"anim_type": "offset", "duration": 0.1, "from": [0,0], "to": [0,-10]}, "loop": False},
    {"type": "text", "speaker": "爱丽克丝", "content": "你昨天答应过我要一起去下层矿洞挖钻石的！你再不起来，我就把你箱子里的熟猪排全吃光！"},

    # ---------------- 分支选项 ----------------
    {
        "type": "menu",
        "title": "要怎么回应她？",
        "choices": [
            {"label": "route_tease", "text": "别动我的猪排！我起还不行吗！"},
            {"label": "route_gentle", "text": "（揉揉眼睛）早安，爱丽克丝。今天你真有精神。"}
        ]
    },

    # 分支A：欢喜冤家
    {"type": "label", "name": "route_tease"},
    {"type": "character_update", "id": "alex", "image": "char_alex_normal", "transition": 0.2},
    {"type": "text", "speaker": "爱丽克丝", "content": "哼，就知道这招对你最管用。"},
    {"type": "jump", "target": "pre_mining"},

    # 分支B：直球出击（加好感度）
    {"type": "label", "name": "route_gentle"},
    {"type": "var", "variable": "alex_affection", "operation": "add", "value": 1},
    {"type": "character_update", "id": "alex", "image": "char_alex_blush", "transition": 0.3},
    {"type": "text", "speaker": "爱丽克丝", "content": "哎？突然说、说什么呢……快点换衣服啦，笨蛋。"},
    {"type": "character_move", "id": "alex", "position": "center_right", "duration": 0.5},
    {"type": "jump", "target": "pre_mining"},

    # ---------------- 准备下矿 ----------------
    {"type": "label", "name": "pre_mining"},
    {"type": "character_update", "id": "alex", "image": "char_alex_smile", "transition": 0.2},
    {"type": "text", "speaker": "爱丽克丝", "content": "烤土豆我放在你熔炉里了，记得吃。我先去矿洞入口把火把和水桶准备好。"},
    {"type": "text", "speaker": "爱丽克丝", "content": "你赶紧去储物箱里拿一把铁镐跟上来。别再用木镐挖煤了！"},
    
    {"type": "character_hide", "id": "alex", "fade_out": 0.5},
	{"type": "text", "speaker": "史蒂夫", "content": "（爱丽克斯总是这样风风火火的……但不得不说，烤土豆真香。）"},
    {"type": "text", "speaker": "史蒂夫", "content": "好吧，先把铁镐找出来再去和她汇合吧。应该就在房间里的箱子里……"},

    # ---------------- 返回游戏寻找物品 ----------------
    # 隐藏UI让玩家在MC里开箱子找铁镐
	# 引擎实现尚未完工，暂时跳过
    # {
    #     "type": "hide_ui_return_game",
    #     "wait_for_event": "",
    #     "event_data": "",
    #     "hint": "请打开周围的箱子，将一把【铁镐】放入背包"
    # },

    # （当玩家拿到铁镐后，恢复UI，从这里继续执行）
    {"type": "var", "variable": "has_pickaxe", "operation": "set", "value": True},
    {"type": "text", "speaker": "史蒂夫", "content": "太好了，耐久还是满的。这下不会挨骂了。"},
    {"type": "text", "speaker": "史蒂夫", "content": "出发去矿洞入口吧！"},
    {"type": "fade_out", "duration": 1.0},

    # ---------------- 场景二：矿洞入口 ----------------
    {"type": "music", "action": "stop", "fade": 1.0},
    {"type": "bg", "image": "textures/modTextures/demo/bg_cave_entrance"},
    {"type": "music", "file": "demo.bgm.cave_ambient", "action": "play"},
    {"type": "fade_in", "duration": 1.0},
    
    {"type": "character_show", "id": "alex", "image": "char_alex_normal", "position": "center"},
    {"type": "text", "speaker": "爱丽克丝", "content": "慢死了！你要是再晚来五分钟，我就一个人下去了。"},
	{"type": "text", "speaker": "爱丽克丝", "content": "入口的僵尸我都清理干净了。铁镐带了吧？"},
    {"type": "text", "speaker": "史蒂夫", "content": "抱歉抱歉，顺手收了一下田里的几颗小麦。看，铁镐带了。"},

    # ---------------- 根据好感度触发不同剧情 ----------------
    {
        "type": "condition",
        "condition": "alex_affection >= 1",
        "true_commands": [
            {"type": "character_update", "id": "alex", "image": "char_alex_blush", "transition": 0.3},
            {"type": "text", "speaker": "爱丽克丝", "content": "给……这个拿着。"},
            {"type": "text", "speaker": "史蒂夫", "content": "这是……刚刚烤好的熟猪排？你没吃掉啊？"},
            {"type": "text", "speaker": "爱丽克丝", "content": "下矿很消耗体力的嘛……我只是顺便多烤了一块而已，才不是特意给你留的！走啦！"}
        ],
        "false_commands": [
            {"type": "character_update", "id": "alex", "image": "char_alex_smile", "transition": 0.2},
            {"type": "text", "speaker": "爱丽克丝", "content": "很好！今天不挖到一组铁矿和半组钻石，我们就不回去！跟紧我哦！"}
        ]
    },

    {"type": "character_hide", "id": "alex", "fade_out": 0.5},
    {"type": "text", "speaker": "史蒂夫", "content": "（看来今天也会是充满冒险的一天呢。）"},

    # ---------------- 结束 ----------------
    {"type": "fade_out", "duration": 1.5},
    {"type": "music", "action": "stop", "fade": 1.5},
    {"type": "return_to_title"}
]