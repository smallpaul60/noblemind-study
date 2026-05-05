#!/usr/bin/env python3
"""
Build chapter-09.html for A Good Name from AGoodName_Chapter9.md.

Uses chapter-08.html as the template (styles + script + page chrome are
identical across all chapters) and substitutes the chapter-specific
content blocks: title, canonical link, dropdown, header, epigraph, body
content, footer nav, and CH_NUM.

The dropdown is built for the FINAL state of the book (with new Ch 9
inserted between current Ch 8 and current Ch 9 — the renumber pass
updates the other chapters' dropdowns to match).
"""

import re
from pathlib import Path

BOOK_DIR = Path(__file__).parent
TEMPLATE = BOOK_DIR / "chapter-08.html"
SRC_MD = BOOK_DIR / "AGoodName_Chapter9.md"
DEST = BOOK_DIR / "chapter-09.html"


# ========================================================================
# Body content for the new Chapter 9, hand-converted from the markdown.
# Markdown structure:
#   **Section Heading**     -> <h2>
#   plain paragraph         -> <p>
#   > *italic quote*        -> <blockquote class="scripture">
#   > — citation            -> <cite>
#   > ***bold-italic***     -> <div class="principle-box">
#   For Further Study list  -> <ul>
#   "One Question to Sit With" + question  -> <h2> + <p><em>...</em></p>
#   "One Thing to Do" + prose -> <h2> + <p>
# Then closing scripture, then reflection-section.
# ========================================================================

BODY_CONTENT = """
        <p>The last chapter was about you.</p>

        <p>It was about how you carry yourself around the young women in your life — how you see them, how you speak to them, how you protect them, how you refuse to use them. That conversation had to come first because it is the one over which you have the most control. You do not get to choose what other people do. You only get to choose what <em>you</em> do, and the man you are becoming is being built one decision at a time, in how you treat the people God puts in your path.</p>

        <p>But there is a second half to that conversation, and we have to have it now.</p>

        <p>Because at some point — maybe soon, maybe years from now — a young woman is going to walk into your life who is more than a friend. Maybe much more. And when that day comes, the question you will need to be able to answer is not just <em>how am I treating her?</em> It is also <em>who is she?</em></p>

        <p>What you are looking for. What you are walking toward. What you are willing to walk away from.</p>

        <p>The standards God gives a young man for the young woman he chooses are not suggestions. They are not opinions. They are not negotiable based on how she makes you feel. God Himself wrote them down, and a young man who loves God will take Him at His word.</p>

        <p>This chapter is about that.</p>

        <div class="principle-box">
          <p><em>You are not lowering the standard. You are raising your eyes to it.</em></p>
        </div>

        <div class="divider">&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;</div>

        <h2>What Scripture Actually Says</h2>

        <p>Paul wrote a letter to a young man named Timothy. Timothy was leading a church and trying to figure out how to navigate the complicated reality of how men and women relate to one another in everyday life. Paul gave him an instruction that is short, clear, and impossible to misunderstand:</p>

        <blockquote class="scripture">
          <p>"Do not sharply rebuke an older man, but rather appeal to him as a father, to the younger men as brothers, the older women as mothers, and the younger women as sisters, in all purity."</p>
          <cite>— 1 Timothy 5:1&ndash;2 (NASB)</cite>
        </blockquote>

        <p>We talked about half of that verse in the last chapter. The half that tells <em>you</em> how to treat a younger woman — as a sister, in all purity. The half that puts the weight on your shoulders.</p>

        <p>But notice what Paul is describing. He is painting a picture of what relationships in the family of God are supposed to look like — fathers, mothers, brothers, sisters — treating one another <em>in all purity.</em> That standard goes both directions. The young woman who fears God carries herself the same way Paul tells you to carry yourself. She treats the young men around her as brothers. In all purity. No games. No flirting for attention. No trying to see how much she can get a young man to do for her.</p>

        <p>That is the kind of young woman you are looking for. A young woman whose first commitment is to God, and whose conduct around young men flows from that commitment. Not a young woman who keeps her purity tucked in her pocket for the right occasion. A young woman who carries it with her into every room, with every young man she meets, whether anyone is watching or not.</p>

        <div class="divider">&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;</div>

        <h2>The Heart vs. the Surface</h2>

        <p>Now we have to deal with something the world is going to tell you is the most important thing about a young woman, and that Scripture says is the least important.</p>

        <p>How she looks.</p>

        <p>You are growing up in a culture that has handed you a checklist — face, body, hair, style, image, presentation. The checklist is everywhere. It is on every screen. It is in every advertisement. It is even in the way some young men talk to one another about young women, ranking and rating them like they were horses at an auction. You have heard it. You may have done it. It is one of the things the screen has done to your eyes.</p>

        <p>Scripture stands directly against all of it.</p>

        <blockquote class="scripture">
          <p>"Charm is deceitful and beauty is vain, but a woman who fears the LORD, she shall be praised."</p>
          <cite>— Proverbs 31:30 (NASB)</cite>
        </blockquote>

        <p>Read it slowly. Charm is <em>deceitful.</em> Beauty is <em>vain.</em> The two qualities the world tells you to chase — the two qualities most young men do chase — are described by God Himself as deceptive and empty. Not bad in themselves. Not sinful to possess. But useless as a foundation for choosing the woman you will spend your life with.</p>

        <p>Charm fades when life gets hard. Beauty fades with time. Both will leave you. And if you built your decision on either of them, you will wake up one day with nothing left to build a life on.</p>

        <p>Peter said the same thing a different way:</p>

        <blockquote class="scripture">
          <p>"Your adornment must not be merely external — braiding the hair, and wearing gold jewelry, or putting on dresses; but let it be the hidden person of the heart, with the imperishable quality of a gentle and quiet spirit, which is precious in the sight of God."</p>
          <cite>— 1 Peter 3:3&ndash;4 (NASB)</cite>
        </blockquote>

        <p>Two words deserve your full attention there: <em>hidden</em> and <em>imperishable.</em></p>

        <p>Hidden — because what you are looking for is not what you can see at first glance. It will not be on her social media. It will not be in the first conversation. The qualities God tells you to look for are buried under the surface, and they take time to discover.</p>

        <p>Imperishable — because the things that matter most are the things that do not fade. Beauty fades. Charm fades. Cleverness fades. The hidden person of the heart, when it has been shaped by the fear of God, is the only thing about a young woman that <em>cannot fade.</em> It is what will still be there when she is eighty years old. It is what will still be there after the hardest year of her life. It is what will still be there when nothing else is.</p>

        <p>A young man who learns to look for the imperishable will save himself a lifetime of regret. A young man who keeps looking at the surface will get exactly what the surface gives him — something that does not last.</p>

        <div class="principle-box">
          <p><em>Train your eyes to look at what God looks at.</em></p>
        </div>

        <div class="divider">&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;</div>

        <h2>The Picture of a Wife</h2>

        <p>The book of Proverbs closes with a portrait. Not a checklist. Not a measuring stick. A portrait of the kind of woman a young man should be looking for.</p>

        <blockquote class="scripture">
          <p>"The words of King Lemuel, the oracle which his mother taught him."</p>
          <cite>— Proverbs 31:1 (NASB)</cite>
        </blockquote>

        <p>That is who is speaking in this chapter. A mother — speaking to her son, the king — about the kind of woman he should look for in a wife. Most people call her the woman of Proverbs 31, or the woman of noble character. Read the whole passage sometime when you have twenty minutes alone. Verses 10 through 31. Read it slowly.</p>

        <p>What you will find is not a list of qualifications. What you will find is a picture of a life. A woman who is trustworthy. A woman whose husband can leave the house in the morning knowing she is not a threat to him, his reputation, his children, or his future. A woman who works hard. Who plans ahead. Who is generous to the poor. Who is wise in how she speaks. Who fears the Lord.</p>

        <p>Her hands are busy. Her mouth is kind. Her household is orderly. Her future is secure. And the people who know her best — her husband and her children — are the loudest in praising her.</p>

        <blockquote class="scripture">
          <p>"An excellent wife is the crown of her husband, but she who shames him is like rottenness in his bones."</p>
          <cite>— Proverbs 12:4 (NASB)</cite>
        </blockquote>

        <p>A crown. Or rottenness in his bones. Solomon does not give a middle option, because there is not one. The young woman you choose will either build you up or eat away at you from the inside. She will either reflect glory onto your life or quietly hollow it out. There is no neutral wife.</p>

        <blockquote class="scripture">
          <p>"House and wealth are an inheritance from fathers, but a prudent wife is from the LORD."</p>
          <cite>— Proverbs 19:14 (NASB)</cite>
        </blockquote>

        <p>Stop and notice what that verse says. Your father can leave you a house. Your father can leave you money. Your father can leave you a name and a reputation. But your father cannot give you a good wife. <em>That gift comes from the Lord Himself.</em></p>

        <p>Which means there is exactly one way to find one. You ask the One who gives them.</p>

        <p>A young man who is choosing a wife on his own — without prayer, without God, without listening for the answer — is trying to do something Scripture says only God can do. Pray for her. Pray about her. And when God answers, recognize the answer.</p>

        <div class="divider">&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;</div>

        <h2>What Faithfulness Looks Like</h2>

        <p>Two women in Scripture — both real, both ordinary in their day, both unforgettable in God's record — show what to look for in a young woman's character <em>before circumstances test it.</em></p>

        <p>The first is Ruth.</p>

        <p>When her husband died and her mother-in-law Naomi prepared to return to a country Ruth did not know — leaving Ruth free to go back to her own people, find another husband, and move on with her life — Ruth said something worth more than any speech a young woman ever made:</p>

        <blockquote class="scripture">
          <p>"Where you go, I will go, and where you lodge, I will lodge. Your people shall be my people, and your God, my God. Where you die, I will die, and there I will be buried. Thus may the LORD do to me, and worse, if anything but death parts you and me."</p>
          <cite>— Ruth 1:16&ndash;17 (NASB)</cite>
        </blockquote>

        <p>Nothing forced her to say it. There was no contract, no audience, no benefit to her. Naomi was an aging widow with nothing left to offer. Going with Naomi meant poverty. It meant being a foreigner. It meant gleaning in fields for a few handfuls of grain at the end of the day.</p>

        <p>And Ruth said: <em>I am going.</em></p>

        <p>That is what loyalty looks like. That is what covenant love looks like in a young woman before she has any reason to perform. Look for that. Look for the young woman who keeps her word when no one is making her keep it. Look for the young woman who does not abandon people when the situation gets hard. Look for the young woman whose loyalty does not depend on what is in it for her.</p>

        <p>The second is Hannah.</p>

        <p>Hannah lived in private grief for years. She wanted a child and could not have one. Another woman in her household mocked her for it. The priest at the temple watched her praying and assumed she was drunk. Her own husband, with the best of intentions, said the wrong thing to comfort her.</p>

        <p>And what did Hannah do?</p>

        <p>She poured her heart out to God in silence. She made a vow. She trusted Him with the deepest sorrow of her life. And when God finally answered and gave her a son — Samuel, who would become one of the great prophets of Israel — Hannah kept her vow and gave him back.</p>

        <blockquote class="scripture">
          <p>"For this boy I prayed, and the LORD has granted me my petition which I asked of Him. So I have also dedicated him to the LORD; as long as he lives he is dedicated to the LORD."</p>
          <cite>— 1 Samuel 1:27&ndash;28 (NASB)</cite>
        </blockquote>

        <p>A young woman who can carry private grief without growing bitter. A young woman who trusts God in seasons when nothing about her life is what she hoped it would be. A young woman who keeps her promises to God when the cost is high.</p>

        <p>Look for that.</p>

        <div class="principle-box">
          <p><em>Watch a young woman in disappointment. That is where you will see who she really is.</em></p>
        </div>

        <div class="divider">&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;</div>

        <h2>What Scripture Warns Against</h2>

        <p>Now we have to look at the other side, because Scripture does not pretend the warning is not there. It puts the warning right in the middle of the wisdom literature so a young man cannot miss it.</p>

        <p>In Proverbs 7, Solomon describes a young man who was naive — that is the word the text uses. The young man wandered into the wrong neighborhood at the wrong time of night, and a woman found him. She had already decided what she was going to do. She had her words ready. She told him her husband was away. She told him no one would know. She flattered him, persuaded him, and led him along.</p>

        <p>We do not need to dwell on the details. Solomon already gives them with restraint, and the warning is what matters:</p>

        <blockquote class="scripture">
          <p>"Suddenly he follows her as an ox goes to the slaughter, or as one in fetters to the discipline of a fool, until an arrow pierces through his liver; as a bird hastens to the snare, so he does not know that it will cost him his life."</p>
          <cite>— Proverbs 7:22&ndash;23 (NASB)</cite>
        </blockquote>

        <blockquote class="scripture">
          <p>"Her house is the way to Sheol, descending to the chambers of death."</p>
          <cite>— Proverbs 7:27 (NASB)</cite>
        </blockquote>

        <p>A young man followed a young woman because she made him feel something. He did not stop to ask who she was. He did not stop to ask where it was going. He did not stop to ask what God said about it. And the road he was on, Solomon says, was the road to death.</p>

        <p>You will meet young women like this. Not all of them, not most of them, but you will meet them. Young women who have already decided what they want from a young man and are simply looking for one naive enough to give it to them. Young women who flatter, who flirt, who push, who persuade. Young women who are not waiting to find out who you are — they are waiting to find out what you will give them.</p>

        <p>Solomon names this woman a second time, a few chapters later:</p>

        <blockquote class="scripture">
          <p>"The woman of folly is boisterous, she is naive and knows nothing. She sits at the doorway of her house, on a seat by the high places of the city, calling to those who pass by, who are making their paths straight..."</p>
          <cite>— Proverbs 9:13&ndash;15 (NASB)</cite>
        </blockquote>

        <p>She is loud. She is sitting where she can be seen. She is calling out to anyone who passes. And she does not know what she does not know — Scripture calls her <em>naive,</em> the same word it uses for the young man she traps. Her foolishness draws in his foolishness, and the result is destruction for both.</p>

        <p>A young man of character recognizes her and keeps walking. Without arguing. Without explaining. Without thinking he can fix her. He simply does not engage.</p>

        <p>But there is another warning Scripture gives that young men almost never hear, because it is unromantic and uncomfortable:</p>

        <blockquote class="scripture">
          <p>"It is better to live in a corner of a roof than in a house shared with a contentious woman."</p>
          <cite>— Proverbs 21:9 (NASB)</cite>
        </blockquote>

        <blockquote class="scripture">
          <p>"It is better to live in a corner of the roof than in a house shared with a contentious woman."</p>
          <cite>— Proverbs 25:24 (NASB)</cite>
        </blockquote>

        <p>Solomon said it twice, almost word for word. When God says something twice in the same book, it is because He wants you to hear it.</p>

        <p>A <em>contentious</em> woman is one who fights, who argues, who picks at, who tears down. The Hebrew word carries the picture of someone who is constantly stirring up conflict — picking, criticizing, refusing to let things rest. Solomon is saying that life with a woman like that is so miserable that a man would rather sleep on the corner of his roof than share a roof with her.</p>

        <p>That is not poetry. That is not exaggeration. That is God's plain warning to a young man, given before he chooses, so he does not learn it the hard way after.</p>

        <p>If a young woman tears people down with her words now — her parents, her friends, her teachers, the people serving her at a restaurant — she will tear <em>you</em> down once she has nothing to lose by doing it. That is not a maybe. That is what Scripture says will happen.</p>

        <p>Watch what she does with her tongue when she is annoyed. Jesus Himself said the principle plainly:</p>

        <blockquote class="scripture">
          <p>"For his mouth speaks from that which fills his heart."</p>
          <cite>— Luke 6:45 (NASB)</cite>
        </blockquote>

        <p>The mouth does not invent what is not already in the heart. It only reveals it. Watch the tongue, and you are watching the heart that drives it. That is who she will be when she is your wife.</p>

        <div class="principle-box">
          <p><em>Charm fades. Beauty fades. A contentious tongue does not.</em></p>
        </div>

        <div class="divider">&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;</div>

        <h2>The Test That Tells the Truth</h2>

        <p>If you cannot rely on what she looks like, and you cannot rely on what she says when she is on her best behavior, what can you rely on?</p>

        <p>Time.</p>

        <p>Paul gave the Galatians a list that has outlasted every culture and every fashion. He called it the fruit of the Spirit:</p>

        <blockquote class="scripture">
          <p>"But the fruit of the Spirit is love, joy, peace, patience, kindness, goodness, faithfulness, gentleness, self-control..."</p>
          <cite>— Galatians 5:22&ndash;23 (NASB)</cite>
        </blockquote>

        <p>Notice that Paul calls it <em>fruit.</em> Singular. Not fruits — fruit. These nine things grow together, on the same tree, in a person whose life is rooted in God's Spirit. You do not get the love and the joy without the patience. You do not get the kindness and the goodness without the self-control. They come together because they grow from the same root.</p>

        <p>So watch.</p>

        <p>Watch how she treats the people who can do nothing for her. The waitress at the restaurant. The kid in the youth group nobody else likes. The grandmother on the porch she has known her whole life. Her younger siblings on a day when she is tired. <em>That</em> is who she is. The way a young woman treats a person who has nothing to offer her tells you everything.</p>

        <p>Watch her self-control when she does not get her way. When the plan changes. When she is hungry. When she is tired. When she is wrong. When you tell her something she did not want to hear. The fruit of the Spirit shows up in pressure, not in comfort. Anyone can be pleasant on a good day. The young woman to look for is the one who is still kind on a hard one.</p>

        <p>Watch how she speaks about people who are not in the room. If she gossips about her friends, she will gossip about you. If she runs down her parents to you, she will run you down to her parents. The tongue that tears down is not selective; it tears down everyone.</p>

        <p>Watch her over time — not weeks, but months, and ideally years. Charm can be performed for a season. Fruit takes a season to grow.</p>

        <div class="divider">&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;</div>

        <h2>The Truth You Have to Hear</h2>

        <p>Now I have to say something no young man wants to hear, and every young man needs to hear it before he makes the biggest decision of his life.</p>

        <p>You cannot change her.</p>

        <p>You will be tempted to think you can. Almost every young man is. You will see a young woman who is beautiful, or charming, or who makes you feel a way no one else has, and you will see clearly the things in her character that are wrong — the temper, the dishonesty, the contention, the foolishness, the worldliness, the lack of fear of God — and you will say to yourself, <em>I can help her grow out of that. Once we are together, she will change.</em></p>

        <p>She almost certainly will not.</p>

        <p>The young woman a young man marries is, with very few exceptions, the same young woman he dated. That is what observation and honest experience consistently show, and it is what Scripture itself assumes when it warns the married man of the contentious wife. The woman of Proverbs 21:9 is described in the context of a man who has <em>already</em> married her. The warning would make no sense if marriage cured the problem. Solomon does not say <em>she used to be that way before he married her.</em> He describes what she is <em>under the same roof he sleeps under</em> — and tells him he would rather sleep on the corner of the roof than continue under it with her.</p>

        <p>The Proverbs warnings about contentious women are not flowery language. They describe what actually happens when a man marries hoping for a change that does not come. He sleeps on the roof. And he watches his children grow up under the influence of a mother whose character he tried to ignore.</p>

        <p>Christ is the only Redeemer. He is the only one who can change a heart. That is His work, not yours. And until He has done that work in a young woman, no amount of love from you is going to do it for Him.</p>

        <p>Your job is not to redeem her. Your job is to <em>discern</em> her. You are looking for evidence that God has already begun His work in her life. You are not signing up to do God's work yourself, because you cannot.</p>

        <div class="principle-box">
          <p><em>You marry the woman she is. Not the woman you hope she will become.</em></p>
        </div>

        <div class="divider">&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;</div>

        <h2>A Word About Walking Away</h2>

        <p>Some of what is in this chapter is hard. So let me say something now that needs saying.</p>

        <p>Walking away from a young woman who does not meet the standard God set is not failure. It is wisdom.</p>

        <p>You will be told by people around you — sometimes by your friends, sometimes by your own loneliness — that you are being too picky. That nobody is perfect. That you should not let a good thing get away. That you will end up alone if you keep holding out for some impossible standard.</p>

        <p>Hear me clearly. The standard God set is not impossible. He set it because He knows what makes a marriage last and what destroys one. He set it for your protection and for the protection of the woman you will one day promise yourself to. He is not asking you to find a perfect woman. He is asking you to find a woman who fears Him — and there are still such young women, even now, even in this culture, even in this generation.</p>

        <p>But you will not find her if you settle for less.</p>

        <p>A young man does not honor God by lowering the standard to keep a young woman who is not there. He honors God by trusting Him enough to wait for one who is. And while he waits, he keeps building his own character — because the kind of young woman who fears God is looking for the kind of young man who fears God, and she will not be impressed by a young man who has not done the work.</p>

        <p>If you are in a situation right now with a young woman who does not meet the standard — who does not fear God, who tears people down with her words, who is asking you to compromise things you have promised God you would not compromise, who is the wrong kind of presence in your life — you can walk away. You should walk away. And one day you will understand that walking away was one of the kindest things you ever did, both to her and to yourself.</p>

        <div class="principle-box">
          <p><em>The right young woman does not require you to become a worse man to keep her.</em></p>
        </div>

        <div class="divider">&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;</div>

        <h2>The Standard Is Not Negotiable</h2>

        <p>This chapter and the last one go together. The first half taught you how to treat a young woman well. This half has taught you what to look for in a young woman who is worth treating that way for the rest of your life.</p>

        <p>The standards are God's. Not your culture's. Not your friends'. Not your own. <em>God's.</em> And the young man who measures by anything less is going to get exactly what that lesser measure produces — something that does not last.</p>

        <p>But the young man who keeps his eyes trained on God's standard, who refuses to be hurried, who walks toward what is imperishable and walks away from what is not — that young man is going to find what God has been preparing for him all along.</p>

        <p>He will find a wife who is a crown.</p>

        <p>He will find a partner whose loyalty does not depend on circumstances.</p>

        <p>He will find a friend who fears the same God he fears, and who will help him fear Him better.</p>

        <p>He will find what Scripture calls <em>good</em> — and what Scripture calls good is what lasts.</p>

        <div class="principle-box">
          <p><em>Settle for nothing less.</em></p>
        </div>

        <div class="divider">&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;</div>

        <h2>For Further Study</h2>

        <p>These passages are the foundation. Read them slowly and let the weight of them settle:</p>

        <ul style="margin: 16px 0 16px 24px; color: var(--text-secondary);">
          <li>Proverbs 31:10&ndash;31 — The portrait of a noble woman</li>
          <li>1 Peter 3:1&ndash;6 — The hidden person of the heart</li>
          <li>Ruth 1:16&ndash;17 — Loyalty without an audience</li>
          <li>1 Samuel 1 — Hannah's private trust</li>
          <li>Galatians 5:22&ndash;23 — The fruit that takes a season to grow</li>
        </ul>

        <div class="divider">&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;</div>

        <h2>One Question to Sit With</h2>

        <p><em>Take the young woman you currently spend the most time around &mdash; friend, classmate, anyone. If you watched her for six months, paying attention to how she treats people who can do nothing for her, what do you think you would see? And what does your honest answer to that question tell you?</em></p>

        <div class="divider">&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;</div>

        <h2>One Thing to Do</h2>

        <p>Open your Bible to Proverbs 31:10&ndash;31 and read it once a week for the next four weeks. Do not read it as a checklist for the young woman you hope to find someday. Read it as a description of what God says is <em>good</em> in a woman. Let your eyes get used to it. Train them to recognize the kind of character Scripture honors. The young man who can read Proverbs 31 and recognize that picture in real life is the young man who will not get fooled by a counterfeit.</p>

        <blockquote class="scripture">
          <p>"Charm is deceitful and beauty is vain, but a woman who fears the LORD, she shall be praised."</p>
          <cite>— Proverbs 31:30 (NASB)</cite>
        </blockquote>

        <section class="reflection-section">
          <div class="reflection-header" onclick="toggleReflection()">
            <h2>Reflection Questions</h2>
            <span class="arrow">&#x25BC;</span>
          </div>
          <div class="reflection-body">
            <div class="reflection-question">
              <span class="q-num">1.</span>
              <span class="q-text">Take the young woman you currently spend the most time around &mdash; friend, classmate, anyone. If you watched her for six months, paying attention to how she treats people who can do nothing for her, what do you think you would see? And what does your honest answer to that question tell you?</span>
              <textarea data-question="1" placeholder="Your thoughts..." rows="3"></textarea>
            </div>
          </div>
        </section>
"""

# ========================================================================
# Final dropdown — Ch 9 NEW chapter inserted, old 9-13 shifted to 10-14.
# ========================================================================

DROPDOWN = '''          <select id="chapter-select" onchange="goToChapter(this.value)">
            <option value="">Jump to...</option>
            <option value="introduction.html">Introduction</option>
            <option value="chapter-01.html">Ch 1: Your Name Is Your Most Valuable Asset</option>
            <option value="chapter-02.html">Ch 2: The Man in the Mirror</option>
            <option value="chapter-03.html">Ch 3: When Nobody's Watching</option>
            <option value="chapter-04.html">Ch 4: Made On Purpose, For a Purpose</option>
            <option value="chapter-05.html">Ch 5: The Relationship You Need Most</option>
            <option value="chapter-06.html">Ch 6: The Bible Isn't What You Think</option>
            <option value="chapter-07.html">Ch 7: Putting Down the Phone</option>
            <option value="chapter-08.html">Ch 8: She Is Somebody's Daughter</option>
            <option value="chapter-09.html" selected>Ch 9: What to Expect from a Young Woman Who Fears God</option>
            <option value="chapter-10.html">Ch 10: The Friends You Choose</option>
            <option value="chapter-11.html">Ch 11: Honor Your Father and Mother</option>
            <option value="chapter-12.html">Ch 12: Work Like It Matters</option>
            <option value="chapter-13.html">Ch 13: Money Will Test Your Character</option>
            <option value="chapter-14.html">Ch 14: The Church Is Not Optional</option>
            <option value="conclusion.html">Conclusion: Your Move</option>
            <option value="scripture-index.html">Scripture Index</option>
          </select>'''


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # 1. <title>
    src = re.sub(
        r"<title>[^<]*</title>",
        "<title>CHAPTER NINE: What to Expect from a Young Woman Who Fears God | Your Name Means Everything: A Good Name</title>",
        src,
        count=1,
    )

    # 2. <link rel="canonical">
    src = re.sub(
        r'<link rel="canonical" href="https://noblemind\.study/A_Good_Name/chapter-08\.html">',
        '<link rel="canonical" href="https://noblemind.study/A_Good_Name/chapter-09.html">',
        src,
        count=1,
    )

    # 3. Replace the dropdown <select>...</select>
    src = re.sub(
        r'\s*<select id="chapter-select".*?</select>',
        "\n" + DROPDOWN,
        src,
        count=1,
        flags=re.DOTALL,
    )

    # 4. Header — chapter-num + h1
    src = re.sub(
        r'<header>\s*<p class="chapter-num">[^<]*</p>\s*<h1>[^<]*</h1>\s*</header>',
        '<header>\n        <p class="chapter-num">CHAPTER NINE</p>\n        <h1>What to Expect from a Young Woman Who Fears God</h1>\n      </header>',
        src,
        count=1,
    )

    # 5. Epigraph
    src = re.sub(
        r'<section class="epigraph">.*?</section>',
        '''<section class="epigraph">
        <blockquote>"Charm is deceitful and beauty is vain, but a woman who fears the LORD, she shall be praised."</blockquote>
        <cite>— Proverbs 31:30 (NASB)</cite>
      </section>''',
        src,
        count=1,
        flags=re.DOTALL,
    )

    # 6. Replace <div class="content">...</div> body. The content div ends
    # right before the <div id="mark-complete"> button.
    src = re.sub(
        r'(<div class="content">).*?(\s*</div>\s*<div id="mark-complete")',
        r"\1" + BODY_CONTENT + r"      </div>\n\n      <div id=\"mark-complete\"",
        src,
        count=1,
        flags=re.DOTALL,
    )

    # 7. Footer-nav: prev = ch-08, next = ch-10 (final state after renumber)
    src = re.sub(
        r'<div class="footer-nav">.*?</div>',
        '''<div class="footer-nav">
          <a href="chapter-08.html">&larr; Ch 8: She Is Somebody's Daughter</a>
          <a href="chapter-10.html">Ch 10: The Friends You Choose &rarr;</a>
        </div>''',
        src,
        count=1,
        flags=re.DOTALL,
    )

    # 8. CH_NUM = 8 -> 9
    src = re.sub(r"const CH_NUM = 8;", "const CH_NUM = 9;", src, count=1)

    DEST.write_text(src, encoding="utf-8")
    print(f"Wrote {DEST}")
    print(f"  Length: {len(src)} bytes, {src.count(chr(10))} lines")


if __name__ == "__main__":
    main()
