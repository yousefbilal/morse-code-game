import pygame
import pygame.gfxdraw
import serial
import random


class Game:
    WIDTH = 800
    HEIGHT = 600
    FPS = 60
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    LIGHT_BLUE = (173, 216, 230)

    MORSE_CODE_DICT = {
        ".-": "A",
        "-...": "B",
        "-.-.": "C",
        "-..": "D",
        ".": "E",
        "..-.": "F",
        "--.": "G",
        "....": "H",
        "..": "I",
        ".---": "J",
        "-.-": "K",
        ".-..": "L",
        "--": "M",
        "-.": "N",
        "---": "O",
        ".--.": "P",
        "--.-": "Q",
        ".-.": "R",
        "...": "S",
        "-": "T",
        "..-": "U",
        "...-": "V",
        ".--": "W",
        "-..-": "X",
        "-.--": "Y",
        "--..": "Z",
        "-----": "0",
        ".----": "1",
        "..---": "2",
        "...--": "3",
        "....-": "4",
        ".....": "5",
        "-....": "6",
        "--...": "7",
        "---..": "8",
        "----.": "9",
    }

    COMSOC_WORDS = [
        "NETWORK",
        "WIRELESS",
        "COMMUNICATION",
        "BROADBAND",
        "SATELLITE",
        "FIBER",
        "MODEM",
        "ROUTER",
        "SWITCH",
        "PROTOCOL",
    ]

    def __init__(self, serial_port: str) -> None:
        self.__ser = serial.Serial(serial_port, 115200, timeout=0.1)

        pygame.init()
        self.__screen = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT), pygame.RESIZABLE
        )
        pygame.display.set_caption("Morse Code Game")
        self.__font = pygame.font.Font(None, 32)
        self.__big_font = pygame.font.Font(None, 92)
        self.__button_font = pygame.font.Font(None, 48)
        self.__title_font = pygame.font.Font(None, 64)
        self.__game_over_font = pygame.font.Font(None, 56)
        self.reset_game()

    def reset_game(self) -> None:
        self.received_morse = ""
        self.received_message = ""
        self.current_symbol = ""
        self.current_morse_code = ""
        self.target_word = random.choice(Game.COMSOC_WORDS)
        self.lives = 3
        self.game_over = False
        self.game_won = False
        self.__ser.flush()
        self.__ser.reset_input_buffer()

    def __display_text(
        self, text: str, font: pygame.font.Font, color: tuple, x: int, y: int
    ) -> None:
        surf = font.render(text, True, color)
        self.__screen.blit(surf, (x, y))

    def __display_center(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple = GREEN,
        x: int | None = None,
        y: int | None = None,
    ) -> None:
        surf = font.render(text, True, color)
        rect = surf.get_rect(
            center=(
                (self.__screen.get_width() // 2) if not x else x,
                (self.__screen.get_height() // 2) if not y else y,
            )
        )
        self.__screen.blit(surf, rect)

    def __display_button(
        self, text: str, x: int, y: int, width: int, height: int
    ) -> pygame.Rect:
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.__screen, Game.BLUE, button_rect)
        pygame.draw.rect(self.__screen, Game.WHITE, button_rect, 2)
        text_surf = self.__button_font.render(text, True, Game.WHITE)
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.__screen.blit(text_surf, text_rect)
        return button_rect

    def __update_display(self) -> None:
        self.__screen.fill(self.BLACK)

        # Display title
        self.__display_text("Morse Code Game", self.__title_font, Game.WHITE, 20, 20)

        # Display game information
        self.__display_text(
            f"Target Word: {self.target_word}", self.__font, Game.WHITE, 20, 100
        )
        self.__display_text(
            f"Received Morse: {self.received_morse}",
            self.__font,
            Game.LIGHT_BLUE,
            20,
            140,
        )
        self.__display_text(
            f"Decoded Message: {self.received_message}",
            self.__font,
            Game.GREEN,
            20,
            180,
        )

        # Display lives
        for i in range(self.lives):
            pygame.gfxdraw.aacircle(
                self.__screen,
                self.__screen.get_width() - 100 + i * 35,
                40,
                15,
                Game.RED,
            )
            pygame.gfxdraw.filled_circle(
                self.__screen,
                self.__screen.get_width() - 100 + i * 35,
                40,
                15,
                Game.RED,
            )

        # Display current symbol
        self.__display_center(self.current_symbol, self.__big_font)

        # Display restart button
        self.restart_button = self.__display_button(
            "Restart",
            self.__screen.get_width() - 150,
            self.__screen.get_height() - 80,
            125,
            50,
        )

        pygame.display.flip()

    def __display_game_over_screen(self) -> None:
        self.__screen.fill(self.BLACK)
        if self.game_won:
            message = "Congratulations! You've won!"
            color = Game.GREEN
        else:
            message = "Game Over! You've run out of lives."
            color = Game.RED

        self.__display_center(message, self.__game_over_font, color, y=200)
        self.__display_center(
            f"The word was: {self.target_word}", self.__font, Game.WHITE, y=300
        )
        self.restart_button = self.__display_button(
            "Play Again",
            self.__screen.get_width() // 2 - 100,
            self.__screen.get_height() // 2 + 100,
            200,
            60,
        )
        pygame.display.flip()

    def __receive_from_esp32(self) -> str | None:
        try:
            if self.__ser.in_waiting:
                return self.__ser.read().decode("utf-8")
            return None
        except UnicodeDecodeError:
            return None

    @classmethod
    def __morse_to_char(cls, morse_code: str) -> str:
        return cls.MORSE_CODE_DICT.get(morse_code, "")

    def __handle_new_symbol(self, new_symbol: str) -> None:
        if new_symbol == " ":
            self.__handle_word_space()
        elif new_symbol == "/":
            self.__handle_letter_space()
        elif new_symbol in [".", "-"]:
            self.__handle_morse_symbol(new_symbol)

    def __handle_word_space(self) -> None:
        self.received_morse += (
            "  "
            if self.received_morse and not self.received_morse.endswith("  ")
            else ""
        )
        self.current_symbol = "Word Pause"
        self.received_message += (
            " "
            if self.received_message and not self.received_message.endswith(" ")
            else ""
        )

    def __handle_letter_space(self) -> None:
        self.received_morse += (
            " " if self.received_morse and not self.received_morse.endswith(" ") else ""
        )
        self.current_symbol = "Letter Pause"
        if self.current_morse_code.strip():
            char = Game.__morse_to_char(self.current_morse_code)
            self.current_morse_code = ""
            if not char or not self.__check_letter_match(char):
                self.lives -= 1
                return
            self.received_message += char

    def __handle_morse_symbol(self, symbol: str) -> None:
        self.received_morse += symbol
        self.current_symbol = symbol
        self.current_morse_code += symbol

    def __check_letter_match(self, char: str) -> None:
        target_length = len(self.received_message.strip())
        if (
            target_length <= len(self.target_word)
            and self.target_word[target_length] != char
        ):
            return False
        return True

    def run(self) -> None:
        clock = pygame.time.Clock()
        running = True
        while running:
            clock.tick(Game.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.restart_button.collidepoint(event.pos):
                        self.reset_game()

            if not self.game_over and not self.game_won:
                new_symbol = self.__receive_from_esp32()
                if new_symbol:
                    print(new_symbol)
                    self.__handle_new_symbol(new_symbol)

                self.__update_display()

                if self.received_message.strip() == self.target_word:
                    print("Congratulations! You've matched the target word.")
                    self.game_won = True

                if self.lives <= 0:
                    print("Game Over! You've run out of lives.")
                    self.game_over = True
            else:
                self.__display_game_over_screen()

        pygame.quit()
        self.__ser.close()
