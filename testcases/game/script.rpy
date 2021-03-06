﻿init python:
    _preferences.text_cps = 100
        
    style.red = Style(style.default)
    style.red.color = "#f00"
        
    style.ruby_style = Style(style.default)
    style.ruby_style.size = 12
    style.ruby_style.xoffset = -18
        
define ruby = Character(None, what_line_leading=10, what_ruby_style=style.ruby_style)

label main_menu:
    return

screen text1:
    frame:
        has vbox
        
        text "Testing bold, color, italics, underline, and strikethrough.":
            bold True
            italic True
            underline True
            strikethrough True
            color "#000"

        text "Testing font and size.":
            font "mikachan.ttf"
            size 30

        text "Testing drop_shadow.":
            drop_shadow [ (2, 2) ]
            drop_shadow_color "#000"
            
        text "Testing outlines.":
           outlines [ (2, "#000", 0, 0) ]
            
        text "Testing changing the kerning value, with AA turned off.":
            kerning 2
            antialias False
            
        null height 10
            
        text "Justification: The quick brown fox jumped over the lazy dogs. The quick brown fox jumped over the lazy dogs. The quick brown fox jumped over the lazy dogs.":
            justify True

        null height 10

        text "Greedy: The quick brown fox jumped over the lazy dogs. The quick brown fox jumped over the lazy dogs. The quick brown fox jumped over the lazy dogs.":
            layout "greedy"
            justify True

        null height 10

        text "Subtitle: The quick brown fox jumped over the lazy dogs. The quick brown fox jumped over the lazy dogs. The quick brown fox jumped over the lazy dogs.":
            language "korean-with-spaces"
            layout "subtitle"
            xalign 0.5
            text_align 0.5
            
        text "ビジュアルノベル、ヴィジュアルノベル（visual novel）とは、コンピュータゲームの一ジャンルである。ビジュアルノベルそれ自体もアドベンチャーゲームの一種に分類される。ノベルゲームやサウンドノベルと呼ばれることもある。":
            font "mikachan.ttf"
        
        text "Min-width & Text_align":
            min_width 400
            text_align 1.0
            
        text "This will be typed out slowly.":
            slow_cps 40
            


label start:
    
    # Text tag tests.
    
    $ ui.saybehavior()
    call screen text1
    
    
    $ a = 42
    $ b = "{b}"
    "42 =/= [a], {{b} =/= [b!q]"
    
    "This line is displayed at normal speed. {cps=200}This is displayed at faster speed.{/cps} {cps=50}This is displayed at slower speed.{/cps} {cps=*.5}This is displayed at half speed.{/cps}"
    
    ruby "Testing ruby: S{rt}s{/rt}ingle, {rb}Word{/rb}{rt}word{/rt}."
    
    "{k=-.5}Kerning can be adjusted by the k tag.{/k}\nKerning can be adjusted by the k tag.\n{k=.5}Kerning can be adjusted by the k tag.{/k}"
    
    "Testing color {color=#f00}red{/color}, {color=#ff0f}yellow{/color}, {color=#00ff00}green{/color}, {color=#0000ffff}blue{/color}."
    
    "Testing size {size=18}absolute{/size}, {size=-6}smaller{/size}, {size=+6}bigger{/size}."
    
    "Testing an {font=mikachan.ttf}alternate font{/font}."
    
    "Testing a {=red}custom text tag{/=red}."
    
    "Testing {b}bold{/b}, {i}italics{/i}, {u}underline{/u}, and {s}strikethrough{/s}."
    "Testing {b}{i}bold italic{/i} and {plain}plain{/plain} tags.{/b}"
    
    "Testing the {a=http://www.renpy.org}hyperlink{/a} tag."

    "Testing the space{space=40}and vspace{vspace=40}tags."

    "Testing paragraph{p}and non-paragraph {w}waits."
    "Testing paragraph{p=1}and non-paragraph {w=1}timed waits."
    "Testing the {w}fast display tag. {fast}There should not have been any waits."
    
    "Testing no-wait mode{nw}"    
    "No-wait mode worked."
    
    
    
    return
    
    
        
        
        
    