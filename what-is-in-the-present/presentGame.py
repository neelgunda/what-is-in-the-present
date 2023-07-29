import pygame
import math
import random
from present import Present
from lives import Lives
from optionButtons import OptionButton
from presents_data import presentsEasy, presentsMedium

class PresentGame:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()  # Initialize the mixer for sound playback

        self.screen_width, self.screen_height = 960, 540
        self.gameDisplay = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.background = pygame.image.load('data/assets/bg.png').convert()
        self.background = pygame.transform.smoothscale(self.background, self.gameDisplay.get_size())
        self.background_music = pygame.mixer.Sound('data/assets/bg_music.wav')
        self.music_channel = pygame.mixer.Channel(1)
        self.music_channel.play(self.background_music, loops=-1)
        self.music_channel.set_volume(.2)

        self.close_button = pygame.transform.scale(pygame.image.load('data/assets/close_button.png'), (65, 65))
        self.mistletoe_banner = pygame.transform.scale(pygame.image.load('data/assets/mistletoe-banner.png'), (420, 150)) 

        self.sound_effect_channel = pygame.mixer.Channel(2)
        self.sound_effect_channel.set_volume(1)

        self.game_over_channel = pygame.mixer.Channel(3)
        self.game_over_music = pygame.mixer.Sound('data/assets/game_over_music.wav')

        self.present_sprite = Present()
        self.present_border = pygame.Rect(420, 60, 305, 320)

        self.FPS = 30
        self.clock = pygame.time.Clock()
        self.sound_start_time = 0

        self.rectangle_dragging = False
        self.offset_x = 0
        self.offset_y = 0
        
        self.current_category = None
        self.used_categories = []
    
        self.selected_option = None
        self.check_answer_clicked = False

        self.shake_intensity = 0.0
        self.max_shake_intensity = 10.0  
        self.sound_channel = pygame.mixer.Channel(0) 

        self.height_shift = 20

        self.lives_sprite = Lives()
        self.lives_lost = 0

        self.current_level = 1
        self.current_score = 0
        self.high_score = 0

        self.display_hint_modal = False
        self.hint_text_font = pygame.font.Font('data/fonts/grinch-font.otf', 45)
        self.max_hint_width = 400

        self.win_game = False
        self.lose_game = False

        self.presentsEasy = presentsEasy
        self.presentsMedium = presentsMedium

        self.difficulty = self.presentsEasy
        self.round_present = None
        self.round_options = []

    def select_present(self, presents):
        # Remove categories that have already been used
        available_categories = [category for category in presents if category not in self.used_categories]

        # Check if all categories have been used, if so, switch to the next level
        if not available_categories:
            if presents == self.presentsEasy:
                # Switch to presentsMedium and reset used_categories
                available_categories = self.presentsMedium
                self.difficulty = self.presentsMedium
                self.used_categories = []
                self.current_level += 1
            else:
                self.win_game = True
                self.play_game_over_music()
                return
        

        # Select a category randomly from the available categories
        self.current_category = random.choice(available_categories)
        self.used_categories.append(self.current_category)

        presents_list = list(self.current_category.values())[0]
        selected_present = random.choice(presents_list)
        return selected_present

    def play_game_over_music(self):
        self.music_channel.stop()
        self.game_over_channel.play(self.game_over_music, loops=-1)
        self.game_over_channel.set_volume(1)

    def create_option_buttons(self):
        self.option_buttons = [
            OptionButton(option["name"], option["sound_file"], (self.screen_width // 2 - 350, 150 + self.height_shift + i * 40))
            for i, option in enumerate(self.round_options)
        ]

    def next_round(self):
        if self.round_present:

            # Get all the options from the current category
            self.round_options = list(self.current_category.values())[0]

            # Set the shake sound for the current round
            self.shake_sound = pygame.mixer.Sound(self.round_present["sound_file"])

            # Shuffle the options to mix up the order
            random.shuffle(self.round_options)

            # Recreate option buttons with the updated options
            self.create_option_buttons()

            # Redraw the display
            self.draw()

    def play_sound(self):
        if not self.sound_channel.get_busy():
            self.sound_channel.play(self.shake_sound)
            self.sound_start_time = pygame.time.get_ticks()

    def play_sound_effect(self, sound):
        self.sound_effect_channel.play(pygame.mixer.Sound(sound))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.present_sprite.rect.collidepoint(event.pos):
                        self.rectangle_dragging = True
                        mouse_x, mouse_y = event.pos
                        self.offset_x = self.present_sprite.rect.x - mouse_x
                        self.offset_y = self.present_sprite.rect.y - mouse_y
                    elif self.button_rect.collidepoint(event.pos):
                        self.check_answer_clicked = True

                    if self.quit_button_rect.collidepoint(event.pos) and (self.lose_game or self.win_game) :
                        pygame.quit()

                    if self.try_again_button_rect.collidepoint(event.pos) and (self.lose_game or self.win_game):
                        self.reset()
                    
                    if self.hint_button_rect.collidepoint(event.pos):
                        self.display_hint_modal = True
                    
                    close_button_rect = self.close_button.get_rect(topleft=(635, 100))
                    if close_button_rect.collidepoint(event.pos):
                        self.display_hint_modal = False
                        print("test")

                    for option_button in self.option_buttons:
                        if option_button.rect.collidepoint(event.pos):
                            self.selected_option = option_button.text
                            for other_button in self.option_buttons:
                                other_button.selected = False
                            option_button.selected = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.rectangle_dragging = False
                    # Snap back the present sprite to its original position if it hits the border
                    if not self.present_border.contains(self.present_sprite.rect):
                        self.present_sprite.rect.clamp_ip(self.present_border)

            elif event.type == pygame.MOUSEMOTION:
                if self.rectangle_dragging:
                    mouse_x, mouse_y = event.pos

                    if self.present_border.collidepoint(mouse_x, mouse_y):
                        self.present_sprite.rect.x = mouse_x + self.offset_x
                        self.present_sprite.rect.y = mouse_y + self.offset_y
                        self.shake_intensity = math.sqrt((event.rel[0] ** 2) + (event.rel[1] ** 2))
                        self.shake_sound.set_volume(min(1.0, self.shake_intensity / self.max_shake_intensity))
                        self.play_sound()

        # Stop sound at 2 seconds
        if self.sound_channel.get_busy() and pygame.time.get_ticks() - self.sound_start_time >= 2000:
            self.sound_channel.stop()

        # Check if right answer is selected
        if self.check_answer_clicked:
            if self.selected_option == self.round_present["name"]:
                self.sound_channel.stop()
                self.play_sound_effect('data/assets/sound_effects/right-answer.wav')
                self.current_score +=  1
                if (self.current_score > self.high_score):
                    self.high_score = self.current_score

                self.round_present = self.select_present(self.difficulty)
                self.check_answer_clicked = False
                self.selected_option = None
                self.button_text = self.button_font.render("Check Answer", True, (255, 255, 255))
                self.next_round()
            else:
                self.play_sound_effect('data/assets/sound_effects/wrong-answer.wav')
                self.check_answer_clicked = False
                self.lives_lost += 1
                if (self.lives_lost == 3):
                    self.lose_game = True
                    self.play_game_over_music()

        return True
    
    def draw_round_number(self):
        font_level = pygame.font.Font('data/fonts/grinch-font.otf', 100)
        font_round = pygame.font.Font('data/fonts/grinch-font.otf', 30)

        level_text = font_level.render("Level " + str(self.current_level), True, (4, 150, 50))

        round_number_text = str(len(self.used_categories))
        round_number_color = (0, 0, 0)
        round_text = font_round.render("Round " + round_number_text + " out of 4", True, round_number_color)

        text_x = 120
        text_y = -36 + self.height_shift

        self.gameDisplay.blit(level_text, (text_x, text_y))
        self.gameDisplay.blit(round_text, (text_x + 30, text_y + 121))
    
    def draw_translucent_surface(self, gameDisplay, width, height, x, y, translucent_color):
        translucent_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(translucent_surface, translucent_color, (0, 0, width, height), border_radius=10)
        gameDisplay.blit(translucent_surface, (x, y))

    def draw(self):
        self.gameDisplay.fill((255, 255, 255))
        self.gameDisplay.blit(self.background, (0, 0))
        
        #Score Display
        self.draw_translucent_surface(self.gameDisplay, 130, 120, 820, 10, (200, 200, 200, 200))
        font_score = pygame.font.Font('data/fonts/grinch-font.otf', 55)
        score_text = font_score.render("Score", True, (4, 150, 50))
        self.gameDisplay.blit(score_text, (830, -3))

        font_score_data = pygame.font.Font('data/fonts/grinch-font.otf', 70)
        score_data_text = font_score_data.render(str(self.current_score), True, (255,51,54))
        self.gameDisplay.blit(score_data_text, (868, 38))

        #Options Display
        self.draw_translucent_surface(self.gameDisplay, 285, 425, 90, 10, (200, 200, 200, 200))
        option_font = pygame.font.Font('data/fonts/text.ttf', 30)
        for option_button in self.option_buttons:
            if option_button.selected:
                pygame.draw.rect(self.gameDisplay, (59,197,105), option_button.rect, border_radius = 5)
            else:
                pygame.draw.rect(self.gameDisplay, (128, 128, 128), option_button.rect, border_radius = 5)

            text = option_font.render(option_button.text, True, (255,255,255))
            text_rect = text.get_rect(center=option_button.rect.center)
            self.gameDisplay.blit(text, text_rect)

        #Check answer button
        pygame.draw.rect(self.gameDisplay, (255,51,54), self.button_rect, border_radius=5)
        self.gameDisplay.blit(self.button_text, (self.button_rect.centerx - self.button_text.get_width() // 2, self.button_rect.centery - self.button_text.get_height() // 2 - 4))

        #Draw Round Numbers
        self.draw_round_number()

        #Display Present Area
        self.draw_translucent_surface(self.gameDisplay, self.present_border.width - 10, self.present_border.height - 10, self.present_border.x + 5, self.present_border.y + 5,  (255, 255, 255, 50))
        self.gameDisplay.blit(self.present_sprite.image, self.present_sprite.rect)
        
        #Display Lives Area
        self.draw_translucent_surface(self.gameDisplay, 186, 60, 20, 450, (200, 200, 200, 200))
        if (self.lives_lost == 0):
            self.gameDisplay.blit(self.lives_sprite.fullLife, (20, 450))
            self.gameDisplay.blit(self.lives_sprite.fullLife, (80, 450))
            self.gameDisplay.blit(self.lives_sprite.fullLife, (140, 450))

        if (self.lives_lost == 1): 
            self.gameDisplay.blit(self.lives_sprite.fullLife, (20, 450))
            self.gameDisplay.blit(self.lives_sprite.fullLife, (80, 450))
            self.gameDisplay.blit(self.lives_sprite.noLife, (147, 460))

        if (self.lives_lost == 2): 
            self.gameDisplay.blit(self.lives_sprite.fullLife, (20, 450))
            self.gameDisplay.blit(self.lives_sprite.noLife, (88, 460))
            self.gameDisplay.blit(self.lives_sprite.noLife, (146, 460))

        if (self.lives_lost == 3): 
            self.gameDisplay.blit(self.lives_sprite.noLife, (30, 460))
            self.gameDisplay.blit(self.lives_sprite.noLife, (88, 460))
            self.gameDisplay.blit(self.lives_sprite.noLife, (146, 460))
            
        #Display Hint button
        self.hint_button_text = self.button_font.render("Get Hint", True, (255, 255, 255))
        self.hint_button_rect = pygame.Rect(260, 452, 180, 58)
        pygame.draw.rect(self.gameDisplay, (14, 150, 50), self.hint_button_rect, border_radius=5)
        self.gameDisplay.blit(self.hint_button_text, (300, 450))

        self.hint_modal_width = 450
        self.hint_modal_height = 350
        self.hint_modal_rect = pygame.Rect( self.screen_width / 2 - self.hint_modal_width / 2, self.screen_height / 2 - self.hint_modal_height / 2, self.hint_modal_width, self.hint_modal_height)

        self.hint_modal_font = pygame.font.Font('data/fonts/grinch-font.otf', 80)
        self.hint_text = self.hint_modal_font.render("Hint", True, (255,51,54))
        if self.display_hint_modal:
            hint_text = self.round_present["hint"]  # Access the hint correctly from the dictionary
            wrapped_hint_lines = self.wrap_text(hint_text, self.hint_text_font)
            pygame.draw.rect(self.gameDisplay, (255, 255, 255), self.hint_modal_rect, border_radius=15)
            self.gameDisplay.blit(self.close_button, (635, 100))
            self.gameDisplay.blit(self.mistletoe_banner, (270, 165))
            self.gameDisplay.blit(self.hint_text, (430, 78))

            # Display the wrapped hint_text
            y_offset = 285
            for line in wrapped_hint_lines:
                hint_text_surface = self.hint_text_font.render(line, True, (0, 0, 0))
                x_offset = (self.gameDisplay.get_width() - hint_text_surface.get_width()) // 2 + 10
                self.gameDisplay.blit(hint_text_surface, (x_offset, y_offset))
                y_offset += hint_text_surface.get_height() - 30

        self.game_over_modal_width = 650
        self.game_over_modal_height = 550
        self.game_over_modal_rect = pygame.Rect( self.screen_width / 2 - self.game_over_modal_width/ 2, self.screen_height / 2 - self.game_over_modal_height / 2, self.game_over_modal_width, self.game_over_modal_height)
            
        button_width = 250 
        button_height = 80
        self.quit_button_rect = pygame.Rect(self.screen_width / 2 - button_width - 20, self.screen_height / 2 + 160, button_width, button_height)  
        self.try_again_button_rect = pygame.Rect(self.screen_width / 2 + 20, self.screen_height / 2 + 160, button_width, button_height) 

        #Display Game Over
        if self.lose_game or self.win_game:
            text = "You Win!"
            if self.lose_game:
                text = "Game Over!"
            self.game_over_text_font = pygame.font.Font('data/fonts/grinch-font.otf', 150)
            self.game_over_text = self.game_over_text_font.render(text, True, (255, 51, 54))
            pygame.draw.rect(self.gameDisplay, (255, 255, 255), self.game_over_modal_rect, border_radius=15)

            if self.lose_game:
                self.gameDisplay.blit(self.game_over_text, (210, -48))
            else:
                self.gameDisplay.blit(self.game_over_text, (272, -48))
            
            self.draw_translucent_surface(self.gameDisplay, 350, 245, 310, 160, (200, 200, 200, 200))

            font_score = pygame.font.Font('data/fonts/grinch-font.otf', 100)
            score_text = font_score.render("Score", True, (0, 0, 0))
            self.gameDisplay.blit(score_text, (385, 125))

            font_score_data = pygame.font.Font('data/fonts/grinch-font.otf', 190)
            score_data_text = font_score_data.render(str(self.current_score), True, (14, 150, 50))
            self.gameDisplay.blit(score_data_text, (440, 164))

            grinch_font = pygame.font.Font('data/fonts/grinch-font.otf', 60)

  
            pygame.draw.rect(self.gameDisplay, (14, 150, 50), self.quit_button_rect, border_radius=10)
            pygame.draw.rect(self.gameDisplay, (255, 51, 54), self.try_again_button_rect, border_radius=10)

            quit_text = grinch_font.render("Quit", True, (255, 255, 255))
            try_again_text = grinch_font.render("Try Again", True, (255, 255, 255))

            self.gameDisplay.blit(quit_text, (self.quit_button_rect.centerx - quit_text.get_width() / 2, self.quit_button_rect.centery - quit_text.get_height() / 2))
            self.gameDisplay.blit(try_again_text, (self.try_again_button_rect.centerx - try_again_text.get_width() / 2, self.try_again_button_rect.centery - try_again_text.get_height() / 2))

           
        pygame.display.update()

    def wrap_text(self, text, font):
        words = text.split(' ')
        lines = []
        current_line = ''

        for word in words:
            test_line = current_line + word + ' '
            test_text = font.render(test_line, True, (0, 0, 0))

            if test_text.get_width() <= self.max_hint_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + ' '
        
        lines.append(current_line)
        return lines

    def reset(self):
         self.used_categories = []
         self.current_level = 1
         self.current_score = 0
         self.lives_lost = 0
         self.lose_game = False
         self.win_game = False
         self.game_over_channel.stop()
         self.music_channel.play(self.background_music, loops=-1)
         self.difficulty = self.presentsEasy
         self.run()
        
    def run(self):
        self.button_width, self.button_height = 225, 50
        self.button_rect = pygame.Rect(self.screen_width // 4 - self.button_width // 2 - 10, self.screen_height // 2 - self.button_height // 2 + 80 + self.height_shift, self.button_width, self.button_height)
        self.button_font = pygame.font.Font('data/fonts/grinch-font.otf', 35)
        self.button_text = self.button_font.render("Check Answer", True, (255, 255, 255))

        self.round_present = self.select_present(self.presentsEasy)
        self.create_option_buttons()
        self.next_round()

        while self.handle_events():
            self.draw()
            self.clock.tick(self.FPS)

        pygame.quit()
