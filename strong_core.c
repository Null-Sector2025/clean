#include <jni.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <stdint.h>

#define ISOLATE_PATH "/data/data/X.auy.Skual/files/.safe_isolate/"

// v1.3.1 扩充恶意关键词库
static const char *danger_keywords[] = {
    "rm -rf /",
    "rm -rf /system",
    "enabled_accessibility_services",
    "ADD_DEVICE_ADMIN",
    "locksettings set-pin",
    "stratum+tcp://",
    "minerd",
    "/dev/block/mmcblk",
    "am start android.app.action.ADD_DEVICE_ADMIN",
    "settings put secure lock",
    "su persist",
    "install-recovery",
    "adb shell dpm set-device-owner",
    "pm set-install-location",
    NULL
};

// 简易MD5辅助函数（简化版，用于文件完整性校验）
static uint32_t md5_simple(const char *path)
{
    FILE *fp = fopen(path, "rb");
    if(!fp) return 0;
    uint32_t sum = 0;
    char ch;
    while(fread(&ch,1,1,fp) > 0) sum += ch;
    fclose(fp);
    return sum;
}

// 检测.sh脚本恶意内容
JNIEXPORT jboolean JNICALL
Java_X_auy_Skual_SafeCore_detectShellRisk(JNIEnv *env, jobject obj, jstring shContent)
{
    if(shContent == NULL) return JNI_FALSE;
    const char *text = (*env)->GetStringUTFChars(env, shContent, NULL);
    int flag = 0;

    for(int i = 0; danger_keywords[i] != NULL; i++)
    {
        if(strstr(text, danger_keywords[i]))
        {
            flag = 1;
            break;
        }
    }
    (*env)->ReleaseStringUTFChars(env, shContent, text);
    return flag ? JNI_TRUE : JNI_FALSE;
}

// SO文件存在性+简易完整性校验
JNIEXPORT jboolean JNICALL
Java_X_auy_Skual_SafeCore_checkSoSecurity(JNIEnv *env, jobject obj, jstring soPath)
{
    const char *path = (*env)->GetStringUTFChars(env,soPath,NULL);
    struct stat st;
    if(stat(path,&st)!=0 || st.st_size < 1024)
    {
        (*env)->ReleaseStringUTFChars(env,soPath,path);
        return JNI_TRUE;
    }
    (*env)->ReleaseStringUTFChars(env,soPath,path);
    return JNI_FALSE;
}

// 获取隐藏隔离文件夹路径
JNIEXPORT jstring JNICALL
Java_X_auy_Skual_SafeCore_getIsolateDir(JNIEnv *env, jobject obj)
{
    return (*env)->NewStringUTF(env, ISOLATE_PATH);
}

// 文件简易完整性校验接口
JNIEXPORT jint JNICALL
Java_X_auy_Skual_SafeCore_getFileCheckSum(JNIEnv *env, jobject obj, jstring filePath)
{
    const char *fp = (*env)->GetStringUTFChars(env,filePath,NULL);
    jint res = md5_simple(fp);
    (*env)->ReleaseStringUTFChars(env,filePath,fp);
    return res;
}
