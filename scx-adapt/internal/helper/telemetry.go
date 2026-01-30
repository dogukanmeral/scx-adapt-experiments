package helper

import (
	"fmt"
	"os"
	"regexp"
	"strconv"
	"strings"
)

// For files structured like: variablename: value
// Use for:
//
//	/proc/stat: procs_running, procs_blocked
func getVariableAsInt(filePath string, variableName string) (int, error) {

	data, err := os.ReadFile(filePath)
	if err != nil {
		return -1, fmt.Errorf("Error occured while reading file '%s': %s\n", filePath, err)
	}

	re := regexp.MustCompile(fmt.Sprintf("^%s", variableName))

	var v string
out:
	for _, line := range strings.Split(string(data), "\n") {
		if re.MatchString(line) {
			v = strings.Fields(line)[1]
			break out
		}
	}

	val, err := strconv.Atoi(v)

	if err != nil {
		return -1, fmt.Errorf("Error occured while converting '%s' to int: %s\n", v, err)
	}

	return val, nil
}

func DiskCurIO() (int, error) {
	diskData, err := os.ReadFile("/proc/diskstats")

	if err != nil {
		return -1, fmt.Errorf("Error occured while reading file '%s': %s\n", "/proc/diskstats", err)
	}

	var curIO int

	for line := range strings.Lines(string(diskData)) {
		if partitionHier := strings.Fields(line)[1]; partitionHier == "0" {

			curIOPartition, err := strconv.Atoi(strings.Fields(line)[11])

			if err != nil {
				return -1, fmt.Errorf("Error occured while converting '%s' to int: %s\n", strings.Fields(line)[11], err)
			}

			curIO += curIOPartition
		}
	}

	return curIO, nil
}

// 1-min 5-min 15-min
// e.g.: 0.10 0.26 0.33
func LoadAvgs() ([]float64, error) {
	loadAvgData, err := os.ReadFile("/proc/loadavg")
	if err != nil {
		return nil, fmt.Errorf("Error occured while reading file '%s': %s\n", "/proc/loadavg", err)
	}

	loadAvgsStr := strings.Fields(string(loadAvgData))[:3]

	loadAvgsFloat := make([]float64, len(loadAvgsStr))

	for i, s := range loadAvgsStr {
		loadAvgsFloat[i], err = strconv.ParseFloat(s, 64)

		if err != nil {
			return nil, fmt.Errorf("Error occured while converting '%s' to float64: %s\n", s, err)
		}
	}

	return loadAvgsFloat, nil
}

type PressureType string

const (
	Cpu    PressureType = "cpu"
	IO     PressureType = "io"
	Memory PressureType = "memory"
)

type PressureOption string

const (
	Some PressureOption = "some"
	Full PressureOption = "full"
)

/*
 	“some” line indicates the share of time in which at least some tasks are stalled on a given resource.
	“full” line indicates the share of time in which all non-idle tasks are stalled on a given resource simultaneously.
*/

// avg10 avg60 avg300 (seconds)
func Pressures(presType PressureType, presOpt PressureOption) ([]float64, error) {
	presFile := fmt.Sprintf("/proc/pressure/%s", presType)

	presData, err := os.ReadFile(presFile)
	if err != nil {
		return nil, fmt.Errorf("Error occured while reading file '%s': %s\n", presFile, err)
	}

	re := regexp.MustCompile(fmt.Sprintf("^%s", presOpt))

	var pressures []float64
	for line := range strings.Lines(string(presData)) {
		if re.MatchString(line) {
			for _, psi := range strings.Fields(line)[1:4] {
				presStr := strings.Split(psi, "=")[1]

				presFloat64, err := strconv.ParseFloat(presStr, 64)

				if err != nil {
					return nil, fmt.Errorf("Error occured while converting '%s' to float64: %s\n", presStr, err)
				}

				pressures = append(pressures, presFloat64)
			}
		}
	}

	return pressures, nil
}
