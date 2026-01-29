/*
Copyright © 2026 NAME HERE <EMAIL ADDRESS>
*/
package cmd

import (
	"fmt"
	"internal/checks"
	"internal/helper"
	"os"

	"github.com/spf13/cobra"
)

// startCmd represents the start command
var startCmd = &cobra.Command{
	Use:   "start-scheduler",
	Short: "Attach a sched_ext scheduler from added schedulers",
	Long:  ``,
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) == 0 {
			fmt.Println("Missing scheduler name as argument. scx-adapt --help to see usage")
			os.Exit(1)
		} else if len(args) == 1 {
			if checks.IsScxRunning() {
				err := helper.StopCurrScx()

				if err != nil {
					fmt.Println(err)
					os.Exit(1)
				}
			}
			err := helper.StartScx(args[0], "/var/lib/scx-adapt/obj")

			if err != nil {
				fmt.Println(err)
				os.Exit(1)
			}

			fmt.Println("Scheduler attached.")
		} else {
			fmt.Println("Too many arguments. scx-adapt --help to see usage")
		}
	},
}

func init() {
	rootCmd.AddCommand(startCmd)

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// startCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// startCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}
