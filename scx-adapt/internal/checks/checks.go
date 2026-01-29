package checks

import (
	"debug/elf"
	"errors"
	"fmt"
	"os"
	"os/exec"
)

func CheckObj(path string) error {
	file, err := os.Open(path)

	if err != nil {
		return fmt.Errorf("Error occured while opening file '%s': %s\n", path, err)
	}

	elfFile, err := elf.NewFile(file)
	if err != nil {
		return fmt.Errorf("Not an object file: %s\n", path)
	}

	if elfFile.Type != elf.ET_REL || elfFile.Machine != elf.EM_BPF {
		return fmt.Errorf("Not a BPF file: %s\n", path)
	}

	hasStructOpsLink := false

	for _, sec := range elfFile.Sections {
		switch sec.Name {
		case ".struct_ops.link":
			hasStructOpsLink = true
		}
	}

	if !hasStructOpsLink {
		return fmt.Errorf("Doesn't include '.struct_ops.link' section: %s\n", path)
	}

	return nil
}

func CheckDir(path string) error {
	info, err := os.Stat(path)
	if os.IsNotExist(err) {
		return fmt.Errorf("Directory does not exist: %s\n", path)
	}

	if !info.IsDir() {
		return fmt.Errorf("Not a directory: %s\n", path)
	}

	return nil
}

func CheckDependencies() error {
	// Check if BPF tool is installed
	whichCmd := exec.Command("which", "bpftool")
	whichCmd.Run()
	err := whichCmd.Err

	if err != nil {
		return fmt.Errorf("'bpftool' is not found in PATH: %s\n", os.Getenv("PATH"))
	}

	// Check if BPF filesystem is mounted
	grepBpfCmd := "mount | grep bpf"
	err = exec.Command("bash", "-c", grepBpfCmd).Err

	if err != nil {
		return fmt.Errorf("Kernel does not have BPF functionalities")
	}

	// Check if sched_ext directory exists
	_, err = os.Stat("/sys/kernel/sched_ext")
	if os.IsNotExist(err) {
		return fmt.Errorf("Kernel does not have sched_ext functionalities")
	}

	return nil
}

func IsScxRunning() bool {
	opsFile := "/sys/kernel/sched_ext/root/ops"
	_, err := os.Stat(opsFile)

	if errors.Is(err, os.ErrNotExist) {
		return false
	}

	return true
}

func CheckScxAdded(scxFilename string, addedScxsPath string) error {
	files, err := os.ReadDir(addedScxsPath)

	if err != nil {
		return fmt.Errorf("Error reading directory '%s': %s\n", addedScxsPath, err)
	}

	for _, e := range files {
		if e.Name() == scxFilename {
			return nil
		}
	}

	return fmt.Errorf("Scheduler '%s' is not found in %s\n", scxFilename, addedScxsPath)
}
