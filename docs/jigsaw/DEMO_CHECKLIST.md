# Demo checklist, 30 Nov

Run every command from the repo root in Git Bash after `unset SSL_CERT_FILE` (PowerShell: `Remove-Item Env:SSL_CERT_FILE`). `<IP>` is the robot's address on the room's network: at home it is 10.0.0.100 (`results/probes/p1.txt`), and in the room it may differ. `<dist>` is the distance in `results/probes/focus_check.md` (Friday step 4). Sentences below assume Friday's turn check (step 5, A13) passed; if it swapped the wording, swap the turn 1 and turn 3 sentences here too.

## The evening before

- [ ] Charge the robot.
- [ ] Network: confirm the laptop and the robot both join the room's network, or pack a travel router and join both to it. Write down `<IP>`, then check: `uv run python scripts/probes/p1_status.py --host <IP>` shows daemon state `running`.
- [ ] Update nothing: no `git pull`, no `uv sync`, no robot, SDK or Windows updates. Use the commit Friday's tests passed on.
- [ ] Copy the 60 s clip from Friday (runbook step 8) to the laptop and play it once.
- [ ] Try the audio fallback once, because its sound call has never run (`scripts/say.py:18`): `uv run python scripts/say.py "Row 2, column 3. Turn it a quarter turn to the left."`
- [ ] Check that the replay folders read correctly on Friday: `grep -E "r0_c0_a000/|r1_c2_a090/|r3_c4_a180/|r5_c1_a000/|r6_c3_a270/" results/physical.csv | cut -d, -f4,5`. Every line should end in `correct`. If a folder does not, pick another angle of that piece whose five frames are all correct.
- [ ] Pack the five pieces below, a spare piece (row 3, column 3) and the green card.

## Thirty minutes before

1. Robot on. Wait until it is on the network (the `p1_status.py` check above passes).
2. Stop the conversation app in the robot's dashboard; it holds the camera and the audio.
3. `uv run python scripts/run_demo.py --source robot --host <IP> --viewer`
4. Open http://127.0.0.1:8765 in the laptop's browser and show that screen on the projector. The viewer serves the laptop only (`jigsaw/viewer/server.py:81`).
5. Lighting: hold the spare piece (row 3, column 3) at `<dist>` over the green card. Expect "Row 3, column 3. ..." with a nod, and a green outline in the viewer. If you hear "Show me the grid side, over the green card." again and again, move out of glare and let the card fill the camera view (anything white behind it counts as paper).
6. Volume: after that sentence, say "again" from the back of the room; the robot repeats it. This code has no volume setting.
7. Ctrl+C, then run step 3 again so the board starts empty. The viewer's reset button clears the page only, not the app's board.

## During: five pieces, in this order

Hold each piece at `<dist>`, grid to the robot, picture toward you, as on Friday. Take it away between pieces so the card is empty.

| # | Piece | Picture as you see it | Expected |
|---|---|---|---|
| 1 | Row 1, column 1 | upright | "Row 1, column 1. It is the right way up." and a nod |
| 2 | Row 2, column 3 | turned a quarter turn clockwise | "Row 2, column 3. Turn it a quarter turn to the left." |
| 3 | Row 4, column 5 | upside down | "Row 4, column 5. Turn it upside down." |
| 4 | Row 6, column 2 | upright, thumb flat across the middle of the grid | after about 15 unread frames, a shake and "Move your fingers to the edge of the piece." or "I cannot read that one. Show me again." Lift the thumb: "Row 6, column 2. It is the right way up." |
| 5 | Row 7, column 4 | turned a quarter turn counter-clockwise | "Row 7, column 4. Turn it a quarter turn to the right." |

A thumb over a single cell is often still read: with a finger in the simulation, 7629 of 10800 reads were still correct. Cover the middle of the grid. A correct read with the thumb on is not a failure. A wrong row, column or turn is a finding: note the piece and turn, change nothing during the demo, and report it afterwards (CLAUDE.md rule 5).

## Fallbacks

- **Wi-Fi fails.** Replay Friday's frames (they are on the laptop that ran the capture, not in git), one presentation per run: `uv run python scripts/run_demo.py --source replay --frames results/frames/r1_c2_a090 --viewer`. Folders for pieces 1 to 5, zero-based names: `r0_c0_a000`, `r1_c2_a090`, `r3_c4_a180`, `r5_c1_a000`, `r6_c3_a270`. Replay plays no sound and moves nothing (`scripts/run_demo.py:7-9`): read the sentence from the terminal or the viewer's status line. Do not pass `results/frames` itself; replay reads only image files directly in the folder (`jigsaw/robot/sources.py:26`), so it would show nothing.
- **Robot audio fails.** No flag sends speech to the laptop while the robot is the source (`scripts/run_demo.py:68-72`). Keep the demo running. For each `announce: ...` line in the terminal, run in a second terminal `uv run python scripts/say.py "<that sentence>"`, or say it yourself.
- **Robot will not connect.** The error names three checks: robot booted, same Wi-Fi, conversation app stopped. Try them once. Then play the 60 s clip in the laptop's video player; no script plays it. Replay (above) also needs no robot.
- **Viewer fails.** Ctrl+C and run without it: `uv run python scripts/run_demo.py --source robot --host <IP>`. The terminal prints each `announce:` and `give up:` line; enlarge the font and show the terminal. If port 8765 is taken, the app logs a warning and runs without the viewer.

## After

1. Wait for the last nod or shake to finish (every gesture ends at neutral, `jigsaw/robot/reachy.py:38-40`), then say "stop" or press Ctrl+C.
2. If the terminal printed "... head left at ...", run `uv run python scripts/probes/p4_nod.py --host <IP> --move`: one nod and then one shake, each ending at neutral, then it prints "done: nod and shake" (`scripts/probes/p4_nod.py:28-30`). Expect the shake; it is part of the probe, not a give-up. So far seen only on the simulator; Friday step 1c checks it on the robot.
3. Power the robot off. Never call `goto_sleep()` (CLAUDE.md rule 7).
