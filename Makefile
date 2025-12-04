BOARD_FQBN := esp32:esp32:esp32doit-devkit-v1
SKETCH := ./esp

BOARD_PORT := $(shell printf "%s " $$(arduino-cli board list | grep -i UNKNOWN | tr -s ' ' | cut -d ' ' -f1)) # My board FBQN isn't recognized by arduino-cli so I identifies it with UNKNOWN
DEBUG_PORT := $(firstword $(BOARD_PORT))
ESP_SRC := $(wildcard $(SKETCH)/*.ino) $(wildcard $(SKETCH)/*.cpp) $(wildcard $(SKETCH)/*.h)


all: compile_esp

# Detect if source got modified since last compilation
build/esp/.compiled: $(ESP_SRC)
	@echo "Compiling for $(BOARD_FQBN)"
	arduino-cli compile --fqbn $(BOARD_FQBN) --build-path ./build/esp $(SKETCH)
	@touch build/esp/.compiled

compile_esp: build/esp/.compiled


upload_esp: compile_esp
	@if [ -z "$(BOARD_PORT)" ]; then \
		echo "No ESP32 detected"; \
		exit 1; \
	fi

	@for p in $(BOARD_PORT); do \
		echo "Uploading to $$p..."; \
		arduino-cli upload -p $$p --fqbn $(BOARD_FQBN) --input-dir ./build/esp $(SKETCH) || exit $$?; \
	done
	@echo "Successfully uploaded $(SKETCH) to $(BOARD_PORT)"

monitor_esp:
	arduino-cli monitor -p $(DEBUG_PORT) -c baudrate=9600 --timestamp

print:
	@echo "Detected ESP32: $(BOARD_PORT)"
	@echo "Selected FQBN: $(BOARD_FQBN)"

clean:
	rm -rf build

