---
movement: mindwars_part
chapter: 97
pov_id: POV-MARA
timeline_id: TL-NULL-DECISION
motif_events: []
hook: "She spends the night trying to hand the field a list of names, and it will not take one."
words: 1336
length_class: normal
status: revised
---
I went into the copper room at nine on the evening of the tenth of April and came out of it at twenty past six the next morning, and I did not achieve any of the five things I went in to do.

The room runs hot with the door shut and I kept it shut because the mesh keeps the bench emitter honest. By two in the morning I had my sleeves rolled and a headache sitting behind my right eye, and by four I had the particular nausea you get from too much coffee and no food, and I mention all of it because the account is otherwise going to read like a person calmly enumerating impossibilities, and that is not what the night was.

The submission had gone in on the sixteenth of March with a phrase in it that I wrote myself and have not been able to put down since. Under the section on reach, describing what the emission would have to cover to answer a synchronized event, I wrote that the affected area would be three counties wide.

I chose that unit deliberately. I would not give a radius, because a radius implies a circle and a centre and a falloff I cannot defend, and I would not give a figure in kilometres, because a figure in kilometres is a number people will draw on a map and then argue about the edge of. Three counties wide is the honest shape of what I know: it is how far the thing reaches, expressed in the only unit I was prepared to commit to in writing.

Having written it, I spent that night trying to make it not be true. All five attempts are in the bench log with times against them.

The first was aiming. We have person-specific addressing and we have had it since the winter; it is the single best piece of work I have ever done and it is the reason any of this is more than weather. If a channel can be resolved to one person on reception, then the obvious thing is to make the emission resolve the same way: raise the quiet only against the pattern, at the address it is using, and leave every other head in the county alone.

It cannot be done and the reason is not engineering. Addressing on reception is a property of listening: you find the narrow relationships that belong to one person and you follow them. The cancellation is not a message sent to an address. It is a subtractive field raised in a volume, and it acts on what is inside the volume because it is inside the volume, in the way that turning off a light acts on everybody in the room. There is no addressee slot in the operation. There is nothing to put an address into. I spent until eleven twenty trying to build a version with one and what I produced was an addressed emission that carries no cancellation and a cancellation that carries no address, which is the same two things I started with, in separate boxes.

The second was bounding. If it cannot be aimed, make it small and give it a hard edge.

At low power the edge is not an edge. It is a gradient over hundreds of metres, and the gradient is where the interesting failures live: partial subtraction, degradation without loss, people at the margin who lose the thread of a sentence and get it back. I can make a hard boundary at the scale of a room with copper, because copper is a wall and a wall is a real edge. I cannot make a wall three counties wide, and at the scale where the field answers a synchronized event the edge is a slope and the slope has people standing on it.

The third was enumerating during. If I cannot choose who, then at least instrument it: know, while it is running, who is being affected and how much, so that the thing is auditable in flight the way a pairing session is.

There is no telemetry of a subtraction. This is the attempt that took the longest because it is the one I most wanted, and I built three versions of a monitoring scheme between midnight and half past two before I understood that I was trying to measure an absence from the outside. The field does not report what it removes. The only instrument that can detect that something has gone from a person's reach is that person, noticing, and telling somebody. Everything else is inference from behaviour, after the fact, across a population, with no way to attribute one person's Tuesday to the field rather than to a bad week and a worse night's sleep.

The fourth was mapping after. Accept the ignorance in flight, and reconstruct the affected set afterwards, properly, with a survey.

You will find the people who noticed. That is who a survey finds: the ones who reached for something, failed, understood what the failure meant, and were willing to say so to a stranger with a clipboard. Everybody who lost something they did not know they had is invisible to that method by construction, and so is everybody who noticed and assumed it was age, or drink, or grief, and so is everybody who never reaches for that particular thing again and therefore never discovers it is gone. I know precisely how that last category feels from the outside because I have watched one person live inside it since July, and it is not a category I can survey.

The fifth was reversal, and I did that one last because I already knew.

There is no additive inverse in the emitter mechanism. I ran the obvious thing anyway at ten past four, on the bench, on a signal generator rather than on any living thing, which is the only place any of this was ever going to be run: raise the cancellation, then raise its inverse and see whether the waveform returns. It does not. The hardware has no inverse operation that restores what its subtraction removed from the measured field. That establishes no clinical fact about relearning or recovery; it establishes that the emitter cannot put anything back by running the physics in reverse. There is no apology in the mechanism.

At about five I did the thing that I am going to be asked about, if anybody ever asks me about any of this properly.

I made a list.

Eleven names, on the back of a printout, of people I know who are inside the extent. My aunt is on it. Ravi is on it. Both operators are on it. It is not a defensible list, it is not a sample, and it is not the list of everybody I care about; it is the eleven people whose names came to me between one thought and the next, and it took me about forty seconds to write and I am not going to reproduce it here.

Then I opened the parameter file and tried to put them in.

The emission is configured by a plain text file. It has fields for frequency, phase, power, duration, ramp, geometry of the emitter array, and about twenty others, and I wrote every one of those fields, so I knew before I started that what I was doing was not going to work. I typed a new key at the bottom, called it exclusions, and put the eleven names after it, and saved it, and ran the loader.

The loader does what a loader does with a key it has never heard of. It read the file top to bottom, took the parameters it recognized, and stopped at the last line it understood.

Unknown key at line 44. Ignored.

Then it loaded every other parameter correctly and reported ready, at twenty past five in the morning, in a hot room, from a piece of software I wrote myself.
