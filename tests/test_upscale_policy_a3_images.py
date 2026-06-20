from tools.upscale_policy_a3_images import (
    GENERATED_DIR,
    UPSCALED_DIR,
    build_output_path,
    build_realesrgan_command,
    iter_generated_images,
)


def test_build_output_path_adds_x4_suffix():
    source = GENERATED_DIR / "a3_policy_01_loop.png"

    assert build_output_path(source) == UPSCALED_DIR / "a3_policy_01_loop_x4.png"


def test_build_realesrgan_command_uses_x4plus_model():
    source = GENERATED_DIR / "a3_policy_01_loop.png"
    output = build_output_path(source)

    command = build_realesrgan_command(source, output)

    assert "-n" in command
    assert "realesrgan-x4plus" in command
    assert "-s" in command
    assert "4" in command
    assert str(source) in command
    assert str(output) in command


def test_iter_generated_images_finds_policy_pngs(tmp_path):
    generated = tmp_path / "generated"
    generated.mkdir()
    (generated / "a3_policy_01_loop.png").write_bytes(b"png")
    (generated / "notes.txt").write_text("ignore", encoding="utf-8")

    found = list(iter_generated_images(generated))

    assert found == [generated / "a3_policy_01_loop.png"]
