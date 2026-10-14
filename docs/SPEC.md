# Smak — кулінарний помічник

Мета: знайти рецепт, зберегти повні деталі офлайн та перетворити інгредієнти на список покупок.
Тема з переліку ReactNativeP35; самостійний проєкт у react-native-final-project.

Expo SDK 57 (create-expo-app 5, blank-typescript), TypeScript, Expo Router.
Екрани: tabs discover/saved/shopping/settings, динамічний meal/[id], shopping/new, onboarding.
Деталі отримують лише ID; root Stack відкриває їх поверх вкладок. push для деталей/форми,
replace після збереження форми та завершення онбордингу.

TheMealDB educational V1 API key 1: server search, categories filter, lookup details.
Loading skeleton, error/retry, empty states; cancellation/timeout and stale response protection.
FlatList primary lists + keyExtractor/ListEmptyComponent; pull-to-refresh on discover and saved.
Context + AsyncStorage for full saved recipes, shopping rows, theme, onboarding and recipe notes.
Storage operations serialized; unsuccessful writes show an error and preserve last saved state.
Corrupt storage never silently overwrites existing data; explicit reset confirmation available.
Theme light/dark, first-run onboarding, image disk cache, offline indication.
Animations: skeleton pulse, button press scale, list/content entrance, shopping completion feedback;
respect reduce-motion preferences.

Warm cream/orange visual language, Ukrainian UI; recipe data remains original English with disclosure.
Responsive widths and portrait/landscape. Manual shopping form validates name/amount length.
Ingredient import deduplicates by recipe+ingredient; repeated imports do not resurrect checked rows.
No fabricated cooking time, nutrition, ingredients, or native device testing.

Delivery: meaningful Git commits, README, 4–6 real screenshots, test report, defense script,
Expo doctor/typecheck/lint/tests, Android/iOS JS exports and runnable Expo project.
Attempt native Android build/verification using available infrastructure; clearly report limits.
