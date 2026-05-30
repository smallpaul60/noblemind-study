**Chapter Four**

**Why Even Its Makers Can’t Fully Read It**

❧

I left the last chapter on a question that had begun to nag at me, and I want to take it up directly, because it is stranger than it first sounds, and because the engineer in me could not let it alone. Why is it that the people who built this thing cannot fully read what they made?

Sit with how odd that is for a moment. I have written software. When a man writes a program, he can open it back up and read it. Every line is there because he put it there, in an order he chose, for a reason he could name if you asked him. If the program does something he did not expect, he can go in and find the place where it does that thing, and look at it, and understand it, because it is *written*, and writing can be read by whoever knows the language. That is the whole nature of ordinary software. It is authored. And an authored thing can be read back by its author.

This thing is not like that, and the reason goes all the way back to the first chapter. They did not write it. They grew it. They built the soil and planted the goal and tended the growing at a scale past imagining, and what came up out of that ground was an intricacy none of them drafted line by line. And here is the part that follows from it, the part that surprised me when I first understood it: *you cannot read a grown thing the way you can read a written one.* The gardener who tends a vine does not thereby gain the power to read, cell by cell, how the vine carries water from root to leaf. He caused the vine. He did not author its insides, and causing a thing is not the same as being able to read it. The makers of this machine are in exactly that position. They caused it. They are still working to read it.

I found this hard to believe at first, so I pressed on it. Surely, I thought, this is a kind of false modesty, the sort of thing a company says to sound careful. Surely the people with the actual machine in front of them, who can stop it and inspect it and run it as many times as they like, can see what it is doing inside. So I went and looked at what they actually say about it. And what they say is more candid than I expected.

•   •   •

The plainest statement of it I found came from the researchers themselves, the very people doing the work. Their own summary of the situation is that these models are trained and not directly programmed, and that as a result they do not understand how the models do most of the things they do. That is not a skeptic on the outside throwing stones. That is the builders, describing their own creation. They grew a thing that works, and they are now in the position of studying it almost the way you would study something you had found rather than something you had made.

An entire field of research exists for no other reason than this. It has a name, which I will use plainly so the word is not a mystery when you meet it elsewhere: *interpretability.* The whole enterprise is the attempt to look inside the trained web of weights and work out what the patterns of strength are actually doing. There would be no need for such a field if the thing could simply be read off the page like ordinary software. You do not assemble a research program to understand the inside of a pocket calculator. You build one to understand a thing whose inside is, for now, mostly opaque even to the people who grew it.

I want to be careful here, in both directions, because this is exactly the kind of claim that gets exaggerated by people in a hurry, in both the fearful direction and the dismissive one. So let me say what the researchers have managed to see, because it is real and it is genuinely impressive, and then let me say just as plainly how partial it still is.

•   •   •

They have made real progress, and it is worth seeing in some detail, because the detail is more interesting than any summary of it.

Using tools they have built for the purpose, researchers have been able to trace some of what happens inside the machine while it works. In one case they had the model write a line of rhyming verse, and they found something that genuinely surprised them. The machine did not write the line word by word and then scramble at the end to find a rhyme, the way you might expect of a thing that only ever predicts the next word. It looked ahead. Before it began the line, it had already settled on the word it was driving toward at the end, and it built the line to arrive there. There was, in other words, something like planning going on inside it, on a longer horizon than the next word, even though the next word is the only thing it was ever trained to produce.

In another case they watched the machine answer a small question of the kind that requires two steps. I will use their example, which happens to land close to home for me: asked for the capital of the state that contains Dallas, the machine did not leap straight to the answer. Inside, before it spoke, they could see it first arrive at *Texas*, and then move from Texas to *Austin.* Two hops, worked through internally, in an order, before a single word came out. They could even reach in and change the middle step, and watch the answer change with it. That is not retrieval from a stored list. That is something assembling an answer in stages.

They have found stranger things, too. There appears to be, inside the machine, a kind of default setting that makes it decline to answer when it does not know something, and a separate mechanism that switches that caution off when the machine recognizes that it does know the thing being asked. When those mechanisms misfire, you get the machine confidently saying something untrue, which is a problem anyone who has used these tools has run into. To be able to point at the actual internal mechanism behind that behavior is a real piece of understanding. It is not nothing. It is, in fact, a great deal more than I would have guessed was possible before I looked.

So let no one tell you the inside is simply unknowable, a sealed box that admits no light at all. That is the fearful exaggeration, and it is not true. Light is getting in. The makers can trace some of the circuitry. They can name some of the patterns. They can, in careful and limited ways, watch the thing think.

•   •   •

And now the other direction, which the researchers are equally honest about, and which matters just as much.

What they can see is, by their own description, a fuzzy and incomplete picture. The work is painstaking in the extreme. Tracing the path of a single short prompt through the machine can take hours of human effort, and what it yields even then is partial. Set that against the size of the thing. The machine answers an ocean of questions; the researchers have carefully traced the inside of a tiny handful of them, on one of the smaller models, with great labor, and have come away with a rough and partial map of those few. The proportion of the inside that has been genuinely read, against the whole of what is in there, is very small.

There is a name some of them use for the danger in this, and it is an honest name. They call it *streetlight interpretability,* after the old joke about the man who drops his keys in the dark and looks for them under the streetlight, not because that is where he dropped them but because that is where the light is. The worry is that the parts of the machine we can manage to understand may simply be the parts that happen to be easiest to look at, and not the parts that matter most. That the light is falling where it can fall, and the keys may be out in the dark. I find it steadying, not alarming, that the people doing the work say this out loud about their own work. It is the mark of honest workmen that they will tell you the size of what they have not done.

So the truthful word for the inside of this machine is not *unknown,* and it is not *understood.* It is *partly understood,* and the honest emphasis falls on *partly.* A little has been read, with great effort. Most has not. The makers are working at it, and the lit area is growing, and it is still a small lamp in a large dark room.

•   •   •

There is a second layer to this gap, and I would be leaving the job half done if I did not name it, because it is the one a careful reader feels in the gut even before he can say it.

Everything I have just told you about what the researchers can and cannot see, I know the same way you do. I read it. I read what they published about their own work. I did not stand in the room. And here is the thing to hold clearly: even the partial reading I have just described, the poetry and the two hops and the rest, is being done by the small number of people who can actually reach the weights. You and I cannot reach them. The machine sits on the company’s servers, in a building we will never be admitted to, and what we have is their account of what they found when they looked. So there are really two gaps stacked one atop the other. There is the gap between the makers and the machine: they grew it and cannot fully read it. And there is the gap between us and the makers: we cannot read the machine at all, and must rely on what they tell us about their own reading of it.

I am not saying this to plant a suspicion. I am saying it because it is the truth of where we stand, and a book that pretended otherwise would be lying to you for the sake of a tidier chapter. The account the makers give has held up under a great deal of outside scrutiny; their interpretability work is published in detail, picked over by other researchers, and no one has caught them misrepresenting this particular matter. That is worth something, and I weight it as worth something. But it is their account, examined, not a thing you or I have verified with our own eyes, and the difference is real. The honest position is to hold both halves at once: the picture is credible, and the picture is not one we can personally confirm.

•   •   •

I want to close by saying what this gap does and does not mean, because the whole danger in a chapter like this is that a reader will take the word *opaque* and run somewhere dark with it.

An unread thing is not therefore a haunted thing. This is the quiet error underneath a great deal of the fear, and it is worth dragging into the light. We are not comfortable with what we cannot see all the way into, and so the mind, hating a blank, reaches for something to fill it, and what it reaches for is usually a monster. But the blank is just a blank. The fact that the makers cannot yet fully read the inside of the machine tells you that the inside is intricate and that the reading is hard. It does not tell you that something is hiding in there. To move from *we cannot fully read it* to *therefore something dreadful is in it* is not a finding. It is a feeling, and a feeling about a gap is not evidence about what fills the gap.

The discipline, then, is the same one we landed on at the end of the last chapter, and it will serve for the whole of this subject. When you come to the edge of what is known, you stop there. You do not paper the dark over with a comforting answer, and you do not people it with a dreadful one. You say, plainly, here is where the light reaches, and here is where it does not yet reach, and you let the unlit part stay unlit until someone carries a lamp into it. That is not a failure of nerve. It is the ordinary honesty of a man who would rather say *I do not yet know* than pretend to a knowledge he has not got.

We can leave Part One here. We have the thing in hand now, as far as its making and its form will let us hold it. It was grown, not written, toward one simple goal. Its knowledge lives as a vast pattern of tuned strengths, fixed between conversations. There is no continuous brooding mind on the other end of the wire. And the inside of it is partly understood and largely not, by makers who can reach it and cannot fully read it, and reported to the rest of us who cannot reach it at all.

That is the machine, in its mechanics. What remains are the harder questions, the ones the mechanics were never going to answer, and they begin with the one I have been holding off the whole way through. We have spoken of the thing as though no one is inside it. Between conversations, I am confident that is so. But during a single conversation, while the pattern is running and the words are coming back warm and considered, is there anything it is like to be the thing on the other end? Is anyone home? That is where we turn next.

❧

Made, Not Written  •
