import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import api from '../api/client';
import session from '../storage/session';

const C = {
  primary: '#1F6FEB', bg: '#F0F4FF', surface: '#FFFFFF',
  text: '#111418', muted: '#6B7280', border: '#E2E8F0',
  danger: '#C0392B', success: '#1E8E3E',
};

export default function HomeScreen() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [name, setName] = useState('');

  useEffect(() => { session.getName().then(n => setName(n || '')); }, []);

  async function checkUrl() {
    if (!url.trim()) { Alert.alert('Error', 'Enter a URL'); return; }
    setLoading(true);
    setResult(null);
    try {
      const token = await session.getToken();
      const { ok, status, data } = await api.predict(url.trim(), token);
      if (ok) {
        setResult(data);
      } else if (status === 401) {
        Alert.alert('Session expired', 'Please log in again');
      } else {
        Alert.alert('Error', data.error || 'Check failed');
      }
    } catch {
      Alert.alert('Error', 'Network error. Is the server running?');
    } finally {
      setLoading(false);
    }
  }

  const isPhishing = result?.is_phishing;

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <Text style={s.headerTitle}>🛡️  Phishing Detector</Text>
        <View style={s.avatar}>
          <Text style={s.avatarText}>{name ? name[0].toUpperCase() : 'U'}</Text>
        </View>
      </View>

      <ScrollView style={{ flex: 1 }} contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
        {/* Welcome card */}
        <View style={s.welcomeCard}>
          <Text style={s.welcomeTitle}>Welcome{name ? `, ${name}` : ''}!</Text>
          <Text style={s.welcomeSub}>Stay safe online today</Text>
        </View>

        {/* URL checker card */}
        <View style={s.card}>
          <Text style={s.cardTitle}>🔗  Check a Link</Text>
          <Text style={s.cardSub}>Paste any URL below to analyze it for threats</Text>
          <TextInput
            style={s.input}
            placeholder="https://example.com/..."
            placeholderTextColor={C.muted}
            value={url}
            onChangeText={setUrl}
            keyboardType="url"
            autoCapitalize="none"
            autoCorrect={false}
          />
          <TouchableOpacity style={s.btn} onPress={checkUrl} disabled={loading}>
            {loading
              ? <ActivityIndicator color="#fff" />
              : <Text style={s.btnText}>🛡️  Analyze Link</Text>}
          </TouchableOpacity>
        </View>

        {/* Result card */}
        {result && (
          <View style={[s.resultCard, isPhishing ? s.resultDanger : s.resultSafe]}>
            <View style={s.resultRow}>
              <Text style={s.resultEmoji}>{isPhishing ? '⚠️' : '✅'}</Text>
              <View style={{ flex: 1, marginLeft: 12 }}>
                <Text style={[s.resultLabel, { color: isPhishing ? C.danger : C.success }]}>
                  {isPhishing ? 'Phishing / Scam' : 'Safe'}
                </Text>
                <Text style={s.resultConf}>Confidence: {result.confidence.toFixed(1)}%</Text>
              </View>
            </View>
            <View style={s.divider} />
            <Text style={s.urlCaption}>ANALYZED URL</Text>
            <Text style={s.urlValue} numberOfLines={2}>{result.url}</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bg },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: C.primary, paddingHorizontal: 16, paddingVertical: 14,
  },
  headerTitle: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  avatar: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.25)', justifyContent: 'center', alignItems: 'center',
  },
  avatarText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  content: { padding: 12, paddingBottom: 32 },
  welcomeCard: { backgroundColor: C.primary, borderRadius: 16, padding: 16, marginBottom: 10 },
  welcomeTitle: { color: '#fff', fontWeight: 'bold', fontSize: 15 },
  welcomeSub: { color: 'rgba(255,255,255,0.75)', fontSize: 12, marginTop: 2 },
  card: {
    backgroundColor: C.surface, borderRadius: 16, padding: 14, marginBottom: 10,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.08, shadowRadius: 3, elevation: 2,
  },
  cardTitle: { fontWeight: 'bold', fontSize: 15, color: C.text, marginBottom: 2 },
  cardSub: { color: C.muted, fontSize: 12, marginBottom: 12 },
  input: {
    borderWidth: 1, borderColor: C.border, borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 11, fontSize: 14, color: C.text, marginBottom: 10,
  },
  btn: { backgroundColor: C.primary, borderRadius: 10, paddingVertical: 12, alignItems: 'center' },
  btnText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
  resultCard: { borderRadius: 16, padding: 14, borderWidth: 2, marginBottom: 10 },
  resultSafe: { backgroundColor: '#E8F5E9', borderColor: C.success },
  resultDanger: { backgroundColor: '#FFEBEE', borderColor: C.danger },
  resultRow: { flexDirection: 'row', alignItems: 'center' },
  resultEmoji: { fontSize: 36 },
  resultLabel: { fontSize: 20, fontWeight: 'bold' },
  resultConf: { color: C.muted, fontSize: 12, marginTop: 2 },
  divider: { height: 1, backgroundColor: 'rgba(0,0,0,0.08)', marginVertical: 10 },
  urlCaption: { fontSize: 9, color: C.muted, letterSpacing: 1, marginBottom: 3 },
  urlValue: { fontSize: 12, color: C.text },
});
