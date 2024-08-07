from PIL import Image, ImageDraw, ImageFont
import discord
import io
from os.path import join, dirname

im = Image.new(mode="RGBA", size=(600, 800), color=(54, 57, 62, 255))

draw = ImageDraw.Draw(im)


def draw_frame(i, avatar_bytes, kit: str, rank: str, name: str):
    # Draw the rounded rectangle
    y = 28 + (64 * i)
    draw.rounded_rectangle((54, y, 594, y + 44), radius=22, fill=(30, 33, 36, 255))

    # ? Draw the avatar image

    # Draw a circle "stroke" around each profile pic
    fill = (0, 0, 0, 0)
    match i:
        case 0:
            fill = (218, 197, 89, 255)
        case 1:
            fill = (181, 181, 181, 255)
        case 2:
            fill = (128, 102, 65, 255)
        case _:
            fill = (0, 0, 0, 255)
    draw.ellipse((38, y - 5, 38 + 52, y + 47), fill=fill)

    # To my future self who has no idea what is going on:
    # 1. We turn the discord avatar into a format we can use
    # 2. We resize this image to 50x50, so that it's the perfect size
    # 3. We create a *mask*, A temporary image, where the white bits = keep, black delete
    # 4. We draw a circle in this mask (which is the size of the full leaderboard). This is where we wanna put the avatar
    # 5. We create a brand new image with same dimensions as the leaderboard, as a temp Image
    # 6. We paste the profile pic into the temp image in the place we want
    # 7. We paste the temp image with the leaderboard but use the mask so that only places in the white circle actually get added
    # 8. This means that the leaderboard gets only a circle crop of the profile pic in the right place

    # Turn the discord asset into an Image
    profile_img = Image.open(io.BytesIO(avatar_bytes))
    profile_img.thumbnail((50, 50))

    # Create a mask to draw
    mask_im = Image.new("L", (600, 800), 0)
    mask_draw = ImageDraw.Draw(mask_im)
    mask_draw.ellipse((40, y - 3, 40 + 48, y + 45), fill=255)

    # Create another temp image, trust
    temp_im = Image.new("RGBA", (600, 800), (0, 0, 0, 0))
    temp_im.paste(profile_img, (40, y - 3))
    im.paste(temp_im, (0, 0), mask_im)

    # ? Draw the kit img
    # TODO: Awaiting new emojis
    img_path = ""
    try:
        img_path = join(dirname(__file__), (kit + "_icon.png"))
    except Exception as e:
        print(
            f"Exception while drawing icon logo in leaderboard for {name}. Probable cause corrupted rank. Icon will look incorrect. \n\n Exact Exception:\n{e}"
        )
        img_path = join(dirname(__file__), "axe_icon.png")

    kit_img = Image.open(img_path)
    kit_img.thumbnail((32, 32))

    im.paste(kit_img, (548, y + 8), kit_img)

    # ? Draw all the text in the frame
    font = ImageFont.truetype(join(dirname(__file__), "JosefinSans.ttf"), size=28)
    font_small = ImageFont.truetype(join(dirname(__file__), "JosefinSans.ttf"), size=20)

    # Draw username
    draw.text((108, y + 12), text=name, font=font)

    # Draw rank
    draw.text((490, y + 12), text=rank, font=font)

    # Draw placement
    draw.text(
        (2, int((y * 1.008) + 12)),  # y * 1.008 because it appeared misaligned
        text=f"#{i+1}",
        fill=(200, 200, 200, 255),
        font=font_small,
    )


async def create_leaderboard(
    members: list[discord.Member | None], highest_kits: list[str], ranks: list[str]
) -> Image:  # type: ignore NO
    # Lot of issues cuz
    usernames = [member.name for member in members if member != None]
    members = [member for member in members if member != None]
    for i in range(len(usernames)):
        avatar_bytes = await members[i].avatar.read()  # type: ignore falsly showing that avatar could be None
        draw_frame(i, avatar_bytes, highest_kits[i], ranks[i], usernames[i])
    print("Done!")
    return im  # type: ignore IDK about this type check ok?
