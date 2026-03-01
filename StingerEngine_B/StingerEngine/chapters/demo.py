# -*- coding: utf-8 -*-
# 剧本：雨后的咖啡香
# 演示了基本的剧情流程、分支选择、变量标记和条件判断等功能

script_data = [
    # === 开场 ===
    {"type": "fade_out", "duration": 1.0},
    {"type": "bg", "image": "black"},
    {"type": "music", "action": "stop"},
    
    {"type": "fade_in", "duration": 2.0},
    {"type": "bg", "image": "bg_cafe_rain"},
    {"type": "music", "file": "bgm_relax", "action": "play"},
    {"type": "sfx", "file": "sfx_rain", "loop": True},

    # 旁白
    {"type": "text", "speaker": "旁白", "content": "窗外的雨淅淅沥沥地下着，已经是下午三点了。"},
    {"type": "text", "speaker": "旁白", "content": "这家名为'时光角落'的咖啡店，今天格外安静。"},

    # 主角独白
    {"type": "text", "speaker": "我", "content": "（呼……终于可以把这周的工作告一段落了。）"},
    {"type": "text", "speaker": "我", "content": "（这种天气，果然还是热咖啡最配啊。）"},

    # === 角色登场 ===
    {"type": "sfx", "file": "sfx_door", "loop": False},
    {"type": "wait", "duration": 0.5},

    # 有请主人公入场
    {"type": "character", "image": "char_yao_normal", "action": "enter", "position": "left"},
    {"type": "text", "speaker": "？？？", "content": "那个……请问！"},
    {"type": "wait", "duration": 0.5},
    {"type": "text", "speaker": "我", "content": "（被突然的声音吓了一跳。）"},

    {"type": "character", "image": "char_yao_normal", "action": "update", "expression": "shocked"},
    {"type": "text", "speaker": "？？？", "content": "啊，抱歉抱歉，我太着急了。"},
    {"type": "text", "speaker": "我", "content": "没关系，请问有什么事吗？"},

    {"type": "character", "image": "char_yao_normal", "action": "update", "expression": "worried"},
    {"type": "text", "speaker": "少女", "content": "那个……我刚才坐在这个位置，好像把一本笔记本忘在这里了。"},
    {"type": "text", "speaker": "少女", "content": "是黑色的，上面贴着一个猫咪贴纸……"},

    # 变量标记
    {"type": "set_var", "variable": "found_notebook", "value": True},
    {"type": "text", "speaker": "我", "content": "（我低头看了看桌角，确实有一本黑色的笔记本。）"},

    # === 第一个分支选择 ===
    {
        "type": "menu",
        "title": "我该怎么回应她？",
        "choices": [
            {"label": "route_polite", "text": "温和地递给她（好感度 +）"},
            {"label": "route_tease", "text": "稍微逗逗她（好感度 不变）"}
        ]
    },

    # === 分支 A：温和路线 ===
    {"type": "label", "name": "route_polite"},
    {"type": "character", "image": "char_yao_normal", "action": "update", "expression": "relieved"},
    {"type": "text", "speaker": "我", "content": "是这个吗？我正想问是谁落下的。"},
    {"type": "action", "name": "play_animation", "anim": "handover"},
    {"type": "text", "speaker": "少女", "content": "太好了！真的是它！谢谢你！"},
    {"type": "set_var", "variable": "favorability", "value": 2},
    {"type": "jump", "target": "common_scene"},

    # === 分支 B：调侃路线 ===
    {"type": "label", "name": "route_tease"},
    {"type": "character", "image": "char_yao_normal", "action": "update", "expression": "normal"},
    {"type": "text", "speaker": "我", "content": "笔记本啊……描述得这么详细，里面有什么秘密吗？"},
    {"type": "character", "image": "char_yao_normal", "action": "update", "expression": "blush"},
    {"type": "text", "speaker": "少女", "content": "啊！没、没什么秘密！只是画稿而已……"},
    {"type": "text", "speaker": "我", "content": "（看着她慌张的样子，我笑了笑，把本子递过去。）"},
    {"type": "text", "speaker": "我", "content": "开玩笑的，给你。"},
    {"type": "set_var", "variable": "favorability", "value": 1},
    {"type": "jump", "target": "common_scene"},

    # === 公共场景 ===
    {"type": "label", "name": "common_scene"},
    {"type": "character", "image": "char_yao_normal", "action": "update", "expression": "smile"},
    {"type": "text", "speaker": "少女", "content": "真的帮大忙了。我叫苏瑶，是附近美院的学生。"},
    {"type": "text", "speaker": "我", "content": "幸会，我是这里的常客。"},

    {"type": "music", "file": "bgm_emotion", "action": "change", "fade": 2.0},
    {"type": "text", "speaker": "苏瑶", "content": "为了表示感谢，这杯咖啡我请你好吗？"},

    # === 第二个分支选择 (结局分支) ===
    {
        "type": "menu",
        "title": "我要接受吗？",
        "choices": [
            {"label": "end_good", "text": "接受邀请，交换联系方式"},
            {"label": "end_normal", "text": "婉拒，只接受咖啡"}
        ]
    },

    # === 结局 A：Good End ===
    {"type": "label", "name": "end_good"},
    # 使用 condition 类型包裹 if/else 逻辑，方便递归执行
    {
        "type": "condition",
        "condition": "favorability >= 1",
        "true_commands": [
            {"type": "character", "image": "char_yao_happy", "action": "update", "expression": "joy"},
            {"type": "text", "speaker": "苏瑶", "content": "太好了！那……可以加个微信吗？下次我请你吃蛋糕！"},
            {"type": "text", "speaker": "我", "content": "好啊，求之不得。"},
            {"type": "sfx", "file": "sfx_click", "loop": False},
            {"type": "bg", "image": "bg_street"},
            {"type": "character", "action": "clear"},
            {"type": "text", "speaker": "旁白", "content": "雨不知什么时候停了。"},
            {"type": "text", "speaker": "旁白", "content": "空气中弥漫着咖啡和泥土的清香。"},
            {"type": "show_image", "image": "img_cg_good"},
            {"type": "text", "speaker": "系统", "content": "【结局：雨后的约定】"}
        ],
        "false_commands": [
            {"type": "jump", "target": "end_normal"}
        ]
    },

    # === 结局 B：Normal End ===
    {"type": "label", "name": "end_normal"},
    {"type": "character", "image": "char_yao_normal", "action": "update", "expression": "slight_sad"},
    {"type": "text", "speaker": "我", "content": "咖啡就不用啦，举手之劳而已。"},
    {"type": "text", "speaker": "苏瑶", "content": "这样啊……好吧，那真的谢谢你了。"},
    {"type": "bg", "image": "bg_street"},
    {"type": "character", "action": "clear"},
    {"type": "text", "speaker": "旁白", "content": "她向我挥挥手，转身走进了雨幕中。"},
    {"type": "text", "speaker": "旁白", "content": "虽然有些遗憾，但这也是不错的午后插曲。"},
    {"type": "show_image", "image": "img_cg_normal"},
    {"type": "text", "speaker": "系统", "content": "【结局：擦肩而过】"},

    # === 结束 ===
    {"type": "fade_out", "duration": 3.0},
    {"type": "music", "action": "stop", "fade": 2.0},
    {"type": "return_to_title"}
]
