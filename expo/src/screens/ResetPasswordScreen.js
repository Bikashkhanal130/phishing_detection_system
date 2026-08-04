import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, ScrollView, KeyboardAvoidingView, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import api from '../api/client';

const C = { primary: '#1F6FEB', bg: '#F0F4FF', surface: '#FFFFFF', text: '#111418', muted: '#6B7280', border: '#E2E8F0' };

export default function ResetPasswordScreen({ route, navigation }) {
  const { email } = route.params;
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);

  async function doReset() {
    if (!code.trim()) { Alert.alert('Error', 'Enter the code sent to your email'); return; }
    if (newPassword.length < 6) { Alert.alert('Error', 'Password must be at least 6 characters'); return; }
    if (newPassword !== confirmPassword) { Alert.alert('Error', 'Passwords do not match'); return; }

    setLoading(true);
    try {
      const { ok, data } = await api.resetPassword(email, code.trim(), newPassword);
      if (ok) {
        Alert.alert('Success', 'Your password has been reset. Please log in.', [
          { text: 'OK', onPress: () => navigation.reset({ index: 0, routes: [{ name: 'Login' }] }) },
        ]);
      } else {
        Alert.alert('Error', data.error || 'Invalid or expired code');
      }
    } catch {
      Alert.alert('Error', 'Network error');
    } finally {
      setLoading(false);
    }
  }

  async function resend() {
    setResending(true);
    try {
      const { ok, data } = await api.forgotPassword(email);
      Alert.alert(ok ? 'Sent' : 'Error', ok ? 'A new code was sent to your email' : (data.error || 'Failed'));
    } catch {
      Alert.alert('Error', 'Network error');
    } finally {
      setResending(false);
    }
  }

  return (
    <SafeAreaView style={s.safe}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={s.container} keyboardShouldPersistTaps="handled">
          <Text style={s.title}>Reset Password</Text>
          <Text style={s.subtitle}>Enter the code sent to{'\n'}{email}, then choose a new password</Text>

          <TextInput
            style={s.otpInput} placeholder="000000" placeholderTextColor={C.muted}
            value={code} onChangeText={setCode}
            keyboardType="number-pad" maxLength={6} textAlign="center"
          />

          <TextInput
            style={s.input} placeholder="New password" placeholderTextColor={C.muted}
            value={newPassword} onChangeText={setNewPassword} secureTextEntry
          />
          <TextInput
            style={s.input} placeholder="Confirm new password" placeholderTextColor={C.muted}
            value={confirmPassword} onChangeText={setConfirmPassword} secureTextEntry
          />

          <TouchableOpacity style={s.btn} onPress={doReset} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>Reset Password</Text>}
          </TouchableOpacity>

          <TouchableOpacity style={s.link} onPress={resend} disabled={resending}>
            <Text style={s.linkText}>{resending ? 'Sending...' : "Didn't get a code? Resend"}</Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bg },
  container: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  title: { textAlign: 'center', fontSize: 26, fontWeight: 'bold', color: C.text, marginBottom: 8 },
  subtitle: { textAlign: 'center', color: C.muted, marginBottom: 24, lineHeight: 22, fontSize: 14 },
  otpInput: {
    backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 10,
    paddingVertical: 14, fontSize: 28, color: C.text, letterSpacing: 12, marginBottom: 16,
  },
  input: {
    backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 10,
    paddingHorizontal: 14, paddingVertical: 12, fontSize: 15, color: C.text, marginBottom: 12,
  },
  btn: { backgroundColor: C.primary, borderRadius: 10, paddingVertical: 14, alignItems: 'center', marginTop: 4, marginBottom: 12 },
  btnText: { color: '#fff', fontWeight: 'bold', fontSize: 15 },
  link: { alignItems: 'center', paddingVertical: 10 },
  linkText: { color: C.primary, fontSize: 14 },
});
