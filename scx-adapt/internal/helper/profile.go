package helper

import (
	"fmt"
	"reflect"

	"github.com/go-playground/validator/v10"
	"gopkg.in/yaml.v3"
)

type Config struct {
	Schedulers []Scheduler `yaml:"schedulers" validate:"required,dive"`
}

type Scheduler struct {
	Path      string    `yaml:"path" validate:"required"`                   // TODO: add: existence of file check and obj check
	Priority  int       `yaml:"priority" validate:"required,gte=1,lte=139"` // TODO: add: priority conflict check
	Criterias Criterias `yaml:"criterias"`
}

type Criterias struct {
	LoadAvg1Min *float32 `yaml:"load_avg_1_min"`
	LoadAvg1Max *float32 `yaml:"load_avg_1_max"`

	LoadAvg5Min *float32 `yaml:"load_avg_5_min"`
	LoadAvg5Max *float32 `yaml:"load_avg_5_max"`

	LoadAvg15Min *float32 `yaml:"load_avg_15_min"`
	LoadAvg15Max *float32 `yaml:"load_avg_15_max"`

	// TODO: add pressures, procs-r, procs-b, diskcurIO
}

func (s Scheduler) Validate() error {
	v := validator.New()

	if err := v.Struct(s); err != nil {
		return err
	}

	r := reflect.ValueOf(s.Criterias)

	for i := 0; i < r.NumField(); i++ {
		if !r.Field(i).IsNil() {
			return nil
		}
	}

	return fmt.Errorf("No criterias are defined in %s", s.Path)
}

func (conf Config) Validate() error {
	for _, s := range conf.Schedulers {
		if err := s.Validate(); err != nil {
			return fmt.Errorf("Error in scheduler '%s': %w", s.Path, err)
		}
	}

	return nil
}

func ValidateYAML(yamlData []byte) error {
	var conf Config
	if err := yaml.Unmarshal(yamlData, &conf); err != nil {
		return err
	}

	if err := conf.Validate(); err != nil {
		return fmt.Errorf("Invalid config: %w", err)
	}

	return nil
}
