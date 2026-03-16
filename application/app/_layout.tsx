import "../global.css";
import {
  DarkTheme,
  DefaultTheme,
  ThemeProvider,
} from "@react-navigation/native";
import { Stack, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useEffect, useRef } from "react";
import "react-native-reanimated";

import { useColorScheme } from "@/hooks/use-color-scheme";
import { AuthProvider, useAuth } from "../context/AuthContext";

export const unstable_settings = {
  anchor: "(tabs)",
};

function RootLayoutNav() {
  const { user, isLoading } = useAuth();
  const segments = useSegments();
  const router = useRouter();
  const colorScheme = useColorScheme();
  const notifListenerRef = useRef<any>(null);

  useEffect(() => {
    if (isLoading) return;

    const inAuthGroup = segments[0] === "(auth)";

    if (!user && !inAuthGroup) {
      // Redirect to login if user is not authenticated and not in auth group
      router.replace("/(auth)/login");
    } else if (user && inAuthGroup) {
      // Redirect to home if user is authenticated and in auth group
      router.replace("/(tabs)");
    }
  }, [user, isLoading, segments]);

  // Global notification tap listener — navigates to Medicines tab
  useEffect(() => {
    const { addNotificationResponseReceivedListener } =
      require("expo-notifications");

    notifListenerRef.current = addNotificationResponseReceivedListener(
      (response: any) => {
        const data = response?.notification?.request?.content?.data;
        if (data?.medicineId) {
          // Navigate to medicines tab when user taps the notification
          router.push("/(tabs)/medicines");
        }
      },
    );

    return () => {
      if (notifListenerRef.current) {
        notifListenerRef.current.remove();
      }
    };
  }, []);

  if (isLoading) {
    return null; // Or a splash screen
  }

  return (
    <ThemeProvider value={colorScheme === "dark" ? DarkTheme : DefaultTheme}>
      <Stack>
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen
          name="modal"
          options={{ presentation: "modal", title: "Modal" }}
        />
      </Stack>
      <StatusBar style="auto" />
    </ThemeProvider>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <RootLayoutNav />
    </AuthProvider>
  );
}
