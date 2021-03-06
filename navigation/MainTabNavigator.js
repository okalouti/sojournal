import React from "react";
import { Platform } from "react-native";
import {
  createStackNavigator,
  createBottomTabNavigator
} from "react-navigation";

import TabBarIcon from "../components/TabBarIcon";
import MapScreen from "../screens/MapScreen";
import Camera from "../screens/Camera";
import SettingsScreen from "../screens/RaspberryPi";
import GroupScreen from "../screens/Groups";

const MapStack = createStackNavigator({
  Group: GroupScreen,
  Map: MapScreen
});

MapStack.navigationOptions = {
  tabBarLabel: "Memories",
  tabBarIcon: ({ focused }) => (
    <TabBarIcon
      focused={focused}
      name={
        Platform.OS === "ios"
          ? `ios-information-circle${focused ? "" : "-outline"}`
          : "md-information-circle"
      }
    />
  )
};

const CameraStack = createStackNavigator({
  Camera: Camera
});

CameraStack.navigationOptions = {
  tabBarLabel: "Upload",
  tabBarIcon: ({ focused }) => (
    <TabBarIcon
      focused={focused}
      name={Platform.OS === "ios" ? "ios-camera" : "md-camera"}
    />
  )
};

const SettingsStack = createStackNavigator({
  Settings: SettingsScreen
});

SettingsStack.navigationOptions = {
  tabBarLabel: "SojournCam",
  tabBarIcon: ({ focused }) => (
    <TabBarIcon
      focused={focused}
      name={Platform.OS === "ios" ? "ios-options" : "md-options"}
    />
  )
};

export default createBottomTabNavigator({
  MapStack,
  CameraStack,
  SettingsStack
});
