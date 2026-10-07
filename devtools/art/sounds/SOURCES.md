# Sound sources

The Chinook's one sound is cut from a recording taken from freesound.org under the Creative Commons
Zero (CC0 1.0) public-domain dedication, which permits use, modification and redistribution without
attribution. The recordist is credited here anyway, because they deserve it. The file in `src/` is
the recording as downloaded (Freesound's high-quality Vorbis preview); `build.py sounds` cuts and
loops it into `src/main/resources/assets/chinook/sounds/` with the shared `tools/sound/cutlib.py`.

| File | Title | Recordist | Freesound page | License |
|---|---|---|---|---|
| `162243-ch-47-chinook.ogg` | Military Aircraft Ambient Noise (aboard a CH-47 Chinook; from a U.S. Government video) | qubodup | https://freesound.org/people/qubodup/sounds/162243/ | CC0 1.0 |

| Shipped sound | Built from |
|---|---|
| `rotor.ogg` | 162243, from 13.728 s, 3.340 s long: 38 blade beats of 88 ms (each rotor's three blades at 225 rpm beat at 11.25 a second) in a recording steady within half a decibel, the start chosen where the 200 ms crossfade's two ends correlate best (0.69), so the beat runs on through the join |
