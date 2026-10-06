# Skyscraper Stack Repair Lab: Submission

## Checklist

- [x] **Before video (10 s):** [before_bug.mp4](before_bug.mp4)
- [x] **After video (10 s):** [after_fixed.mp4](after_fixed.mp4)
- [ ] **LLM chat link:** _paste link here_

An extra 17-second video, [after_full_demo.mp4](after_full_demo.mp4), climbs all the way to the edge of space.

The videos were recorded from the actual game code at 60 FPS. A script pressed the keys instead of a person. Each video has a caption bar along the bottom and shows each key press in the top-right corner.

## What the before video shows (original code)

- Dropping a block squarely onto the tower makes it collapse straight away.
- Off-centre drops that still overlap the tower collapse it too, so the tower can never be built.
- On the collapse screen, Space does nothing. Only R restarts.

At the start, every drop overlaps the tower: the block and the tower are both 180px wide, and the arena is too narrow to drop clear of it. With the inverted check, that means every early drop collapses the tower.

## What changed

| Task | Change | Where |
|---|---|---|
| 1. Overlap bug | The drop check was `overlap <= 0`, which is backwards. It is now `overlap > 0`, so landing on the tower stacks and a complete miss collapses it. | `game/game_engine.py`, `drop_block` |
| 2. Perfect placement | A drop within 5px of the tower's edge snaps into place with no trim. A "PERFECT!" message shows the bonus: 2× the streak, up to +10. From the second perfect in a row, the block grows back 10px, up to the starting width. | `place_perfect` |
| 3. Debris | The trimmed overhang falls under gravity and spins as it goes. A complete miss sends the whole block tumbling. | `game/effects.py`, `Debris` |
| 4. Changing sky | The background gradient moves through five stages (sunrise, day, upper sky, violet, space) as the tower grows. Stars fade in near the top, and the ground scrolls out of view. | `render_background` |

**Other fixes, to match the README's expected behaviour:**
- Space now restarts after a collapse. There is a half-second pause first, so a fast drop press doesn't skip the collapse screen.
- The camera scrolls smoothly instead of jumping.
- New blocks always move toward the tower.
- The HUD shows Height and Score separately, on a panel that stays readable against every sky colour.
- The README's folder layout now lists the real files.

## Run it

```bash
pip install pygame
python main.py
```
