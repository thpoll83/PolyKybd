# Key-press samples

Single mechanical keystrokes for the tutorial video's soundtrack (`render/tutorial_audio.py`,
`PK_KEYS=<set>`). Each file is one stroke cut from a Freesound recording, peak-normalised and
faded out; each press in the video draws one stroke of its set at random. A set with
`<set>_up_<n>.wav` files also plays a release when the key comes back up in the picture
(`PK_KEY_UP` scales it, default 1.6 times the recorded level).

All four recordings are CC0 (public domain dedication), so no attribution is required. The
authors are credited here anyway:

| Set | Source | Author | Strokes |
|---|---|---|---|
| `xemptful` | [Single Key Presses on Mechanical Keyboard](https://freesound.org/people/Xemptful/sounds/660387/) | Xemptful | 6 |
| `mxbrown` | [Keyboard - Press down](https://freesound.org/people/Foxfire-/sounds/570754/) (Cherry MX Brown) | Foxfire- | 1 |
| `largekey` (default) | [Single_Key_Stroke_Large_Key](https://freesound.org/people/Capt.Jack/sounds/813210/) | Capt.Jack | 1 press (75–187 ms) and its release (`largekey_up_1`, 185–330 ms), both at the recording's own level |
| `tactile` | [Keyboard_Tactile_8](https://freesound.org/people/StavSounds/sounds/766639/) | StavSounds | 1 |

They were cut from Freesound's public high-quality MP3 previews.
