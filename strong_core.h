#ifndef STRONG_CORE_H
#define STRONG_CORE_H

#include <jni.h>

#ifdef __cplusplus
extern "C" {
#endif

JNIEXPORT jboolean JNICALL
Java_X_auy_Skual_SafeCore_detectShellRisk(JNIEnv *env, jobject thiz, jstring shContent);

JNIEXPORT jboolean JNICALL
Java_X_auy_Skual_SafeCore_checkSoSecurity(JNIEnv *env, jobject thiz, jstring soPath);

JNIEXPORT jstring JNICALL
Java_X_auy_Skual_SafeCore_getIsolateDir(JNIEnv *env, jobject thiz);

JNIEXPORT jint JNICALL
Java_X_auy_Skual_SafeCore_getFileCheckSum(JNIEnv *env, jobject thiz, jstring filePath);

#ifdef __cplusplus
}
#endif

#endif
