### ShadowWalker

This repo contains the code for a DnD/ShadowRun style RPG and BlackJack.  Code was written over about a 6 week period, and some code is in hacker-quality shape, where code like server.py has been refactored a couple of times and is in a more refined state. It's all rough, but some of it is less rough than others. 

## Repo Layout

The main idea was to encourage social interaction between participants, encourage activity outside, and provide some fun for a weekend getaway. 

The client code in the main directory of this repo contains the code that runs on the Player Device (PD), and the servers directory contains the server-side code for both the encounters and blackjack. The client device is an M5StickC Plus2. 

The server code for the encounters (servers\server.py) also runs on the same M5StickC Plus2, and the Blackjack server (servers\blackjack.py) ran on an M5Stack Core2. 

The StickC is fairly memory limited, and some design decisions couldn't be implemented due to memory constraints, so tradeoffs were made in both the client and server side for the RPG.

## Design Goals and Decisions

There are several quality-of-life features included as well, such as an update mechanism and menu system.

The initial design critera included 6 "Chapters" or "Encounters" that lived on independent M5StickC Plus2 "server" devices that were physically separated, and had no communication between them.

ESPNOW was chosen as the communcation protocol between the client and server devices since it is stateless, requires no additional overhead like persistent 802.11 connections, TCP, or higher-level protocols. The packet size is limited to 250 bytes and is fairly fire-and-forget.

Since the player player device is untrusted and both the code on the player device as well as the player data file (player.json), a minimal integrity check is generated and validated on the server-side. 

During encounters and blackjack, all business logic is performed on the server, the player object is modified based on the outcome of server-side activity, the player data is signed using a "secret" key shared between all the server devices plus the MAC Address of the individuals player device, and an "update" packet is sent.

Encounters / Chapters (these words will be used interchangably) are included in the servers\encounters directory, and should be copied to a server device as "encounter.json" depending on which encounter you would like that device to serve. server.py should be copied to the server device as main.py so the encounter runs on boot. 

## Encounter Flow

The RPG is divided into 6 encounters included in the servers\encounters\. These files represent an encounter that happens at a physical location, and when the encounter is concluded, the player's "chapter" is incremented by one, and they are eligible for the next encounter at the next physical location. Hints and pointers are given to move them to the next physical location containing the next encounter. 

When a player arrives at that location, and "minplayers" is met, the server device broadcasts a "Join Encounter" packet containing the summary from the encounter JSON and QR code containing a link to a webpage containing a narrative. The narrative sets the stage for the phases of the encounter, and starts a timer so the webpage can be read. This is kinda hardcoded at 90 seconds just because.  When a player presses Button B for "In?," the QR code is displayed. There are some timing issues here that I worked out in the Blackjack, but they were never backported to the Campaign. #TODO.

From there, the Player Device enters a while loop waiting for encounter-related packets. Speaking of, the Player Device code is ugly and mostly hackish, and I never got around to refactoring it.  One day. :) The server-side code processes the Phases of the Encounter, prompts players for actions, gets theirs responses, processes those, and sends Status packets back to the Player Devices. Rinse and Repeat until the phase is complete, then send the status message between phases, and move on the the next phase. 

## Encounter JSON Format

The encounter JSON has a pretty self-explanatory structure, and is processed top-to-bottom. The encounter metadata is sent to players, Phases are sub-encounters within the encounter processed, when Phases are completed the status message is sent, and when all phases are complete the Encounter outro QR code is sent. 

## Phase Format

The Phases contain a list of enemies, allies, reward, and status.

Enemies, Allies, and Players all use the Player() class. Enemies and Allies may also have customer attackdie and damagedie defined that will be used for their attacks. Enemies will have a "vulnerableto" attribute defined that contains a list of what attack types they are vulnerable to.  Enemies may also have 'xp' and 'ny' defined that are transferred to the player that defeated that enemy. That player will recieve all of the ny and xp from that enemy. At the end of the phase, the xp and ny amounts are divided among all existing players.


