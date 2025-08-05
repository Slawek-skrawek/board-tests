import command
import config

# Path containing the Mynewt project
# PROJECTS_DIR = config.BASE_PATH
# BSP_DIR_PATH = f"{config.TARGET_PATH}repos/apache-mynewt-core/hw/bsp/"
# Path containing the Mynewt bsp directories
BSP_DIR = "@apache-mynewt-core/hw/bsp/"
BOOT_BUILD_PROFILE = "optimized"
BUILD_PROFILE = "debug"

def create_target_name(board_name, app_name):
    return board_name + "-" + app_name

def target_exists(name):
    success, _ = command.run_cmd(f"newt target show {name}", check=False)
    return success

def create_target(target_name):
    if not target_exists(target_name):
        print(f"Creating target: {target_name}")
        command.run_cmd(f"newt target create {target_name}")
    else:
        print(f"Target {target_name} already exists.")

def set_target(target_name, board_name, app_name, print_output=False):
    if app_name == "boot":
        success, output = command.run_cmd(f"newt target set {target_name} app=@mcuboot/boot/mynewt")
    else:
        success, output = command.run_cmd(f"newt target set {target_name} app=apps/{app_name}")
    if print_output:
        print(output)
    success, output = command.run_cmd(f"newt target set {target_name} bsp={BSP_DIR}{board_name}")
    if print_output:
        print(output)
    if app_name == "boot":
        success, output = command.run_cmd(f"newt target set {target_name} build_profile={BOOT_BUILD_PROFILE}")
    else:
        success, output = command.run_cmd(f"newt target set {target_name} build_profile={BUILD_PROFILE}")
    if print_output:
        print(output)

def build_target(target_name, print_output=False):
    print(f"Building target: {target_name}")
    success, output = command.run_cmd(f"newt build {target_name}", check=False)
    if print_output:
        print(output)
    if not success:
        print(output)
        print(f"Build failed for {target_name}:\n{output}")
        return

def create_image(target_name, print_output=False):
    print(f"Creating image for target: {target_name}")
    success, output = command.run_cmd(f"newt create-image {target_name} timestamp", check=False)
    if print_output:
        print(output)
    if not success:
        # print(output)
        print(f"Image creation failed for {target_name}:\n{output}")
        return

def load_image(target_name, print_output=False):
    print(f"Loading target: {target_name}")
    success, output = command.run_cmd(f"newt load {target_name}", check=print_output)
    if print_output:
        print(output)
    if not success:
        print(output)
        print(f"Load failed for {target_name}:\n{output}")
        return

def full_create_target(target_name, board_name, app_name):

    create_target(target_name)
    set_target(target_name, board_name, app_name)
    build_target(target_name)
    if app_name != "boot":
        create_image(target_name)



def main():
            # command.run_cmd(f"cd {PROJECTS_DIR}")
    #for entry in os.scandir(BSP_DIR):
        #if entry.is_dir():
            board_name = "nordic_pca10090" #pic32mx470_6lp_clicker
            #board_name = entry.name
            print(f"\nProcessing target board: {board_name}")

            app_name = "boot"
            target_name = create_target_name(board_name, app_name)
            full_create_target(target_name, board_name, app_name)

            app_name = "blinky"
            target_name = create_target_name(board_name, app_name)
            full_create_target(target_name, board_name, app_name)

            app_name = "watchdog"
            target_name = create_target_name(board_name, app_name)
            full_create_target(target_name, board_name, app_name)

            print(f"Done with {board_name}")
            print("-" * 40)

if __name__ == "__main__":
    main()
