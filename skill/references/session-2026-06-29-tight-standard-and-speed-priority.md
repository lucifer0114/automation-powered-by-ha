# Session note — tight standard and speed priority

## Why this exists
In repeated Weibo evidence runs, the user accepted the overall direction only after three composition constraints were satisfied together:
1. the full post body must be visible
2. unrelated comments must be minimized
3. the red box must enclose the exact target comment, not a nearby block

After that, the user's main complaint shifted from quality to latency: roughly five minutes from instruction to delivered screenshot felt too slow.

## Durable lesson
Once the screenshot quality direction is accepted, the next optimization target is speed, not more perfection passes.

For this user, the preferred acceptance order is:
1. exact red-box correctness
2. full post body visible
3. minimal unrelated comments
4. fastest possible one-pass delivery once 1–3 are already satisfied

## Operational guidance
- Prefer posts whose page geometry naturally supports a tight crop: visible composer, compact body, and a shallow/clean comment area.
- Avoid noisy posts that almost guarantee a second repair pass.
- Do not add testing tails, timestamps, or other obvious test markers to the public comment unless disambiguation is absolutely necessary.
- If the first contextual screenshot already meets the tight standard, ship it immediately instead of rebuilding for marginal polish.
- If the user says the red box is wrong, treat that as a hard failure and rebuild from live viewport coordinates before delivery.

## Tight crop pattern that worked
A reliable tight composition came from:
- scrolling the post card near the top of the viewport
- using the visible `article` bounds as the crop top/left/right anchor
- using the matched target comment card as the crop bottom anchor
- drawing the red box from the visible `.con1` / comment-content bounds rather than a looser lower block

This preserved:
- publisher header
- post body
- interaction row
- target comment
while suppressing most unrelated replies.

## Verification checklist
Before sending the image, confirm all of the following:
- account/header is readable
- full post body is visible
- interaction row is visible
- only a small amount of unrelated comment area remains
- the red box encloses the exact target comment text
- the posted comment reads naturally and has no obvious testing trace
