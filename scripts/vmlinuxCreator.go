package main

import (
	"fmt"
	"os"
	"os/exec"
)

func main() {
	if len(os.Args) != 2 {
		fmt.Println("Specify path to vmlinux.h as only argument.")
		os.Exit(1)
	}

	vmlinuxPath := os.Args[1]

	generateCmd := exec.Command("bpftool", "btf", "dump", "file", "/sys/kernel/btf/vmlinux", "format", "c")

	outFile, err := os.Create(vmlinuxPath)
	if err != nil {
		panic(err)
	}
	defer outFile.Close()
	generateCmd.Stdout = outFile

	err = generateCmd.Start()
	if err != nil {
		panic(err)
	}
	generateCmd.Wait()
}
