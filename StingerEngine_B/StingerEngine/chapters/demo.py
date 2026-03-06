# -*- coding: utf-8 -*-
# 剧本：雨后的咖啡香
# 演示了基本的剧情流程、分支选择、变量标记、条件判断以及好感度解锁隐藏选项

script_data = [
    # === 开场 ===
    {"type": "var", "variable": "favorability", "operation": "set", "value": 0},
    {"type": "bg", "image": "textures/modTextures/demo/bg_cafe_rain"},
    {"type": "fade_in", "duration": 2.0},
    {"type": "music", "file": "demo.bgm.relax", "action": "play"},

    {"type": "text", "speaker": "", "content": "窗外的雨淅淅沥沥地下着，已经是下午三点了。"},
    {"type": "text", "speaker": "", "content": "这家名为'时光角落'的咖啡店，今天格外安静。"},

    # 主角独白
    {"type": "text", "speaker": "我", "content": "（呼……终于可以把这周的工作告一段落了。）"},
    {"type": "text", "speaker": "我", "content": "（这种天气，果然还是热咖啡最配啊。）"},

    # === 角色登场 ===
    {"type": "sfx", "file": "demo.sfx.door_open", "loop": False},
    {"type": "wait", "duration": 0.5},

    # 有请主人公入场
    {"type": "character_enter", "id": "yao", "image": "textures/modTextures/demo/char_yao_normal", "position": "left", "fade_in": 0.5},
    {"type": "text", "speaker": "？？？", "content": "那个……请问！"},
    {"type": "wait", "duration": 0.5},
    {"type": "text", "speaker": "我", "content": "（被突然的声音吓了一跳。）"},

    {"type": "character_update", "id": "yao", "image": "textures/modTextures/demo/char_yao_shocked"},
    {"type": "text", "speaker": "？？？", "content": "啊，抱歉抱歉，我太着急了。"},
    {"type": "text", "speaker": "我", "content": "没关系，请问有什么事吗？"},

    {"type": "character_move", "id": "yao", "position": "center","pause": False, "duration": 0.3},
    {"type": "character_update", "id": "yao", "image": "textures/modTextures/demo/char_yao_worried"},
    {"type": "text", "speaker": "少女", "content": "那个……我刚才坐在这个位置，好像把一本笔记本忘在这里了。"},
    {"type": "text", "speaker": "少女", "content": "是黑色的，上面贴着一个猫咪贴纸……"},

    # 变量标记
    {"type": "var", "variable": "found_notebook", "operation": "set", "value": True},
    {"type": "text", "speaker": "我", "content": "（我低头看了看桌角，确实有一本黑色的笔记本。）"},
 
    # === 第一个分支选择 ===
    {
        "type": "menu",
        "title": "我该怎么回应她？",
        "choices": [
            {"label": "route_polite", "text": "温和地递给她"},
            {"label": "route_tease", "text": "稍微逗逗她"}
        ]
    },

    # === 分支 A：温和路线 ===
    {"type": "label", "name": "route_polite"},
    {"type": "character_update", "id": "yao", "image": "textures/modTextures/demo/char_yao_relieved"},
    {"type": "text", "speaker": "我", "content": "是这个吗？我正想问是谁落下的。"},
    # {"type": "action", "name": "play_animation", "animdata": },
    {"type": "text", "speaker": "少女", "content": "太好了！真的是它！谢谢你！"},
    {"type": "var", "variable": "favorability", "operation": "add", "value": 2},
    {"type": "jump", "target": "common_scene"},

    # === 分支 B：调侃路线 ===
    {"type": "label", "name": "route_tease"},
    {"type": "character_update", "id": "yao", "image": "textures/modTextures/demo/char_yao_normal"},
    {"type": "text", "speaker": "我", "content": "笔记本啊……描述得这么详细，里面有什么秘密吗？"},
    {"type": "character_update", "id": "yao", "image": "textures/modTextures/demo/char_yao_blush"},
    {"type": "text", "speaker": "少女", "content": "啊！没、没什么秘密！只是画稿而已……"},
    {"type": "text", "speaker": "我", "content": "（看着她慌张的样子，我笑了笑，把本子递过去。）"},
    {"type": "text", "speaker": "我", "content": "开玩笑的，给你。"},
    {"type": "jump", "target": "common_scene"},

    # === 公共场景 ===
    {"type": "label", "name": "common_scene"},
    {"type": "character_update", "id": "yao", "image": "textures/modTextures/demo/char_yao_smile"},
    {"type": "text", "speaker": "少女", "content": "真的帮大忙了。我叫苏瑶，是附近美院的学生。"},
    {"type": "text", "speaker": "我", "content": "幸会，我是这里的常客。"},

    {"type": "music", "file": "demo.bgm.emotion", "action": "change", "fade": 2.0},
    {"type": "text", "speaker": "苏瑶", "content": "为了表示感谢，这杯咖啡我请你好吗？"},

    # === 第二个分支选择：好感度影响菜单选项 ===
    {
        "type": "condition",
        "condition": "favorability >= 1",
        "true_commands": [
            {
                "type": "menu",
                "title": "我要接受吗？",
                "choices": [
                    {"label": "end_good_high", "text": "接受邀请，交换联系方式"},
                    {"label": "end_normal", "text": "婉拒，只接受咖啡"},
                    {"label": "end_special", "text": "邀请她一起坐（选项已解锁）"}
                ]
            }
        ],
        "false_commands": [
            {
                "type": "menu",
                "title": "我要接受吗？",
                "choices": [
                    {"label": "end_good_low", "text": "接受邀请"},
                    {"label": "end_normal", "text": "婉拒，只接受咖啡"}
                ]
            }
        ]
    },

    # === 结局：好感足够，接受邀请（Good End） ===
    {"type": "label", "name": "end_good_high"},
    {"type": "character_update", "id": "yao", "image": "textures/modTextures/demo/char_yao_happy"},
    {"type": "text", "speaker": "苏瑶", "content": "太好了！那……可以加个好友吗？下次我请你吃蛋糕！"},
    {"type": "text", "speaker": "我", "content": "好啊，求之不得。"},
    {"type": "sfx", "file": "demo.sfx.bell_click", "loop": False},
    {"type": "character_clear", "fade_out": 0.5},
    {"type": "text", "speaker": "", "content": "雨不知什么时候停了。"},
    {"type": "text", "speaker": "", "content": "空气中弥漫着咖啡和泥土的清香。"},
    {"type": "text", "speaker": "系统", "content": "【结局：雨后的约定】"},
    {"type": "jump", "target": "the_end"},

    # === 结局：好感不足，接受邀请（普通结局） ===
    {"type": "label", "name": "end_good_low"},
    {"type": "character_update", "id": "yao", "image": "textures/modTextures/demo/char_yao_smile"},
    {"type": "text", "speaker": "苏瑶", "content": "那我去点单，你稍等一下。"},
    {"type": "text", "speaker": "我", "content": "嗯，麻烦你了。"},
    {"type": "text", "speaker": "", "content": "她端来咖啡，简单聊了几句天气，便回到自己的座位。"},
    {"type": "text", "speaker": "", "content": "虽然没能深交，但这次偶遇也算温暖。"},
    {"type": "character_clear", "fade_out": 0.5},
    {"type": "text", "speaker": "系统", "content": "【结局：淡淡的咖啡香】"},
    {"type": "jump", "target": "the_end"},

    # === 结局：隐藏选项（特殊结局） ===
    {"type": "label", "name": "end_special"},
    {"type": "character_update", "id": "yao", "image": "textures/modTextures/demo/char_yao_happy"},
    {"type": "text", "speaker": "我", "content": "不如一起坐吧，反正店里人不多，可以聊聊天。"},
    {"type": "text", "speaker": "苏瑶", "content": "诶？可以吗？太好了！"},
    {"type": "text", "speaker": "", "content": "她高兴地坐到对面，拿出素描本翻给我看她的画作。"},
    {"type": "text", "speaker": "苏瑶", "content": "其实我经常来这里找灵感，今天的雨景特别美。"},
    {"type": "text", "speaker": "我", "content": "难怪你的画里总有一种宁静的感觉。"},
    {"type": "text", "speaker": "", "content": "我们聊了很久，从绘画到音乐，从咖啡到旅行。"},
    {"type": "text", "speaker": "苏瑶", "content": "那个……如果不介意，我想为你画一张速写，当作谢礼。"},
    {"type": "text", "speaker": "我", "content": "我的荣幸。"},
    {"type": "character_clear", "fade_out": 0.5},
    {"type": "show_image", "image": "img_cg_special", "fade": 1.5},
    {"type": "text", "speaker": "系统", "content": "【结局：雨中的素描】"},
    {"type": "jump", "target": "the_end"},

    # === 结局 B：婉拒（Normal End） ===
    {"type": "label", "name": "end_normal"},
    {"type": "character_update", "id": "yao", "image": "textures/modTextures/demo/char_yao_slight_sad"},
    {"type": "text", "speaker": "我", "content": "咖啡就不用啦，举手之劳而已。"},
    {"type": "text", "speaker": "苏瑶", "content": "这样啊……好吧，那真的谢谢你了。"},
    {"type": "character_clear", "fade_out": 0.5},
    {"type": "text", "speaker": "", "content": "她向我挥挥手，转身走进了雨幕中。"},
    {"type": "text", "speaker": "", "content": "虽然有些遗憾，但这也是不错的午后插曲。"},
    {"type": "text", "speaker": "系统", "content": "【结局：擦肩而过】"},
    {"type": "jump", "target": "the_end"},

    # === 结束 ===
    {"type": "label", "name": "the_end"},
    {"type": "music", "action": "stop", "fade": 2.0},
    {"type": "fade_out", "duration": 3.0},
    {"type": "return_to_title"}
]