# Jimmy — CC0 humanoid test rig

Source: https://github.com/madjin/100avatars (100Avatars_003)
Author: Polygonal Mind · Licence: CC0 (declared in the file's VRM meta)

Here as a SECOND rig to test the first-person view fix against. One model
cannot show whether a fix is general, and this one differs from `boy.glb` in
the two ways that matter:

  * Mixamo naming (`mixamorig:Head`, `mixamorig:Neck`), which the engine's
    joint lookup — matching "Head" and "head" exactly — does not find at all.
  * NO eye joints. Its VRM humanoid map declares 52 bones and neither
    `leftEye` nor `rightEye` is among them.

So the current approach, which reads the rig's eye joints, produces no
correction whatsoever on this model. That is the argument for deriving the view
from the head MESH rather than from joints.
