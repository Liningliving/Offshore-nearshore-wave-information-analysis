import infodynamics.measures.continuous.kraskov.*;

/** Shared requested settings for synthetic integration and final zero-lag estimates. */
public final class SharedEstimatorSettings {
  public static final String[] KEYS={"k","NORMALISE","NORM_TYPE","DYN_CORR_EXCL","USE_GPU","NOISE_LEVEL_TO_ADD","NOISE_SEED","NUM_THREADS"};
  public static final String[] VALUES={"4","true","MAX_NORM","45","false","1e-8","20261031","1"};
  public static void apply(MutualInfoCalculatorMultiVariateKraskov1 c)throws Exception{for(int i=0;i<KEYS.length;i++)c.setProperty(KEYS[i],VALUES[i]);c.setProperty("TIME_DIFF","0");}
  public static void apply(ConditionalMutualInfoCalculatorMultiVariateKraskov1 c){for(int i=0;i<KEYS.length;i++)c.setProperty(KEYS[i],VALUES[i]);}
  public static void verify(MutualInfoCalculatorMultiVariateKraskov1 c)throws Exception{for(int i=0;i<KEYS.length;i++)verifyValue(KEYS[i],VALUES[i],c.getProperty(KEYS[i]));}
  public static void verify(ConditionalMutualInfoCalculatorMultiVariateKraskov1 c){for(int i=0;i<KEYS.length;i++)verifyValue(KEYS[i],VALUES[i],c.getProperty(KEYS[i]));}
  private static void verifyValue(String key,String wanted,String actual){
    if(actual==null)throw new IllegalStateException("Missing Java property "+key);
    boolean matches=key.equals("NOISE_LEVEL_TO_ADD")?Double.parseDouble(wanted)==Double.parseDouble(actual):wanted.equalsIgnoreCase(actual);
    if(!matches)throw new IllegalStateException("Java property "+key+" expected "+wanted+" got "+actual);
  }
}
