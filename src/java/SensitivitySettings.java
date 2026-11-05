import infodynamics.measures.continuous.kraskov.*;

/** Only k and physical-window-to-index conversion vary from Step 7. */
public final class SensitivitySettings {
  public static int windowTicks(double hours,double unit){
    double ticks=hours/unit;
    if(hours<=0||unit<=0||ticks!=Math.rint(ticks)||ticks>Integer.MAX_VALUE)throw new IllegalArgumentException("Window not integral in index units");
    return (int)ticks;
  }
  public static void verify(MutualInfoCalculatorMultiVariateKraskov1 c,int k,int ticks)throws Exception {
    for(int i=0;i<SharedEstimatorSettings.KEYS.length;i++)check(SharedEstimatorSettings.KEYS[i],wanted(i,k,ticks),c.getProperty(SharedEstimatorSettings.KEYS[i]));
  }
  public static void verify(ConditionalMutualInfoCalculatorMultiVariateKraskov1 c,int k,int ticks){
    for(int i=0;i<SharedEstimatorSettings.KEYS.length;i++)check(SharedEstimatorSettings.KEYS[i],wanted(i,k,ticks),c.getProperty(SharedEstimatorSettings.KEYS[i]));
  }
  static String wanted(int i,int k,int ticks){return i==0?""+k:i==3?""+ticks:SharedEstimatorSettings.VALUES[i];}
  static void check(String key,String wanted,String actual){
    if(actual==null||!(key.equals("NOISE_LEVEL_TO_ADD")?Double.parseDouble(wanted)==Double.parseDouble(actual):wanted.equalsIgnoreCase(actual)))throw new IllegalStateException("Settings mismatch: "+key);
  }
}
