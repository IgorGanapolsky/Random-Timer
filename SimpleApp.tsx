import React from 'react';
import {View, Text, StyleSheet} from 'react-native';

const SimpleApp = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>SuperPassword App</Text>
      <Text style={styles.subtext}>React Native CLI Working!</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5FCFF',
  },
  text: {
    fontSize: 20,
    textAlign: 'center',
    margin: 10,
    fontWeight: 'bold',
  },
  subtext: {
    fontSize: 16,
    textAlign: 'center',
    color: '#333333',
    marginBottom: 5,
  },
});

export default SimpleApp;