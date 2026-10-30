import java.io.*;
import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.KdTree;

/** Focused installed-jar test; deliberately detects row/time mismatch, not a patched estimator. */
public class TheilerIntegrationCheck {
  static class MI extends MutualInfoCalculatorMultiVariateKraskov1 {
    KdTree tree() throws Exception { ensureKdTreesConstructed(); return kdTreeJoint; }
    int actualK(){ return k; } int actualWindow(){ return dynCorrExclTime; }
    boolean exclusionEnabled(){ return dynCorrExcl; }
  }
  static class CMI extends ConditionalMutualInfoCalculatorMultiVariateKraskov1 {
    KdTree tree() throws Exception { ensureKdTreesConstructed(); return kdTreeJoint; }
    int actualK(){ return k; } int actualWindow(){ return dynCorrExclTime; }
    boolean exclusionEnabled(){ return dynCorrExcl; }
    int[] dimensions(){ return new int[]{dimensionsVar1,dimensionsVar2,dimensionsCond}; }
  }
  static boolean hasField(Class<?> c,String name) {
    while(c!=null){ try{c.getDeclaredField(name); return true;}catch(NoSuchFieldException e){c=c.getSuperclass();} } return false;
  }
  static boolean hasTracking(Class<?> c){for(Method m:c.getMethods())if(m.getName().equals("addObservationsTrackObservationIDs"))return true;return false;}
  static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
  static void configure(MI c)throws Exception{c.setProperty("k","4");c.setProperty("DYN_CORR_EXCL","45");c.setProperty("NOISE_LEVEL_TO_ADD","0");c.setProperty("NUM_THREADS","1");c.setProperty("USE_GPU","false");}
  static void configure(CMI c)throws Exception{c.setProperty("k","4");c.setProperty("DYN_CORR_EXCL","45");c.setProperty("NOISE_LEVEL_TO_ADD","0");c.setProperty("NUM_THREADS","1");c.setProperty("USE_GPU","false");}
  static boolean[][] masks(KdTree tree,int n)throws Exception{
    boolean[][] mask=new boolean[n][n];
    for(int i=0;i<n;i++){int[] indices=new int[n+1];tree.findPointsWithinR(i,Double.POSITIVE_INFINITY,45,true,mask[i],indices);}
    return mask;
  }
  public static void main(String[] args)throws Exception{
    Path out=Path.of(args[0]);Files.createDirectories(out);
    int n=240;int[] hours=new int[n];double[][] ho=new double[n][1],hn=new double[n][1],tp=new double[n][1],direction=new double[n][2];
    Random rng=new Random(20261030);
    for(int i=0;i<n;i++){
      hours[i]=i<80?i:i<160?i+10:i+80;
      ho[i][0]=2+rng.nextDouble(); hn[i][0]=ho[i][0]*.7+rng.nextDouble()*.4;
      tp[i][0]=8+2*rng.nextDouble();double theta=rng.nextDouble()*2*Math.PI;
      direction[i][0]=Math.cos(theta);direction[i][1]=Math.sin(theta);
    }
    MI mi=new MI();configure(mi);mi.initialise(1,1);mi.setObservations(ho,hn);
    CMI period=new CMI();configure(period);period.initialise(1,1,1);period.setObservations(tp,hn,ho);
    CMI cmi=new CMI();configure(cmi);cmi.initialise(2,1,1);cmi.setObservations(direction,hn,ho);
    check(mi.actualK()==4&&mi.actualWindow()==45&&mi.exclusionEnabled(),"MI properties not active");
    check(cmi.actualK()==4&&cmi.actualWindow()==45&&cmi.exclusionEnabled(),"CMI properties not active");
    check(period.actualK()==4&&period.actualWindow()==45&&period.exclusionEnabled(),"period CMI properties not active");
    check(Arrays.equals(cmi.dimensions(),new int[]{2,1,1}),"Direction not passed jointly");
    double miValue=mi.computeAverageLocalOfObservations(),cmiValue=cmi.computeAverageLocalOfObservations(),periodValue=period.computeAverageLocalOfObservations();
    check(Double.isFinite(miValue)&&Double.isFinite(cmiValue)&&Double.isFinite(periodValue),"Nonfinite information estimate");
    check(mi.getNumObservations()==n&&cmi.getNumObservations()==n&&period.getNumObservations()==n,"Unexpected observation loss");
    boolean[][] mm=masks(mi.tree(),n), cm=masks(cmi.tree(),n), pm=masks(period.tree(),n);
    int mismatches=0,falseAllowed=0,falseExcluded=0;
    try(PrintWriter rows=new PrintWriter(out.resolve("observation_indices.csv").toFile());PrintWriter pairs=new PrintWriter(out.resolve("pair_eligibility.csv").toFile())){
      rows.println("csv_row,jidt_effective_index,expected_elapsed_hour");
      pairs.println("row_i,row_j,elapsed_hours,row_distance,expected_eligible,mi_eligible,cmi_direction_eligible,cmi_period_eligible");
      for(int i=0;i<n;i++){
        rows.println(i+","+i+","+hours[i]);
        for(int j=i+1;j<n;j++){
          boolean expected=hours[j]-hours[i]>45;
          check(mm[i][j]==(j-i>45),"Installed implementation does not match documented row semantics");
          check(mm[i][j]==cm[i][j]&&mm[i][j]==pm[i][j],"MI and CMI use different exclusion masks");
          if(expected!=mm[i][j]){mismatches++;if(mm[i][j])falseAllowed++;else falseExcluded++;}
          pairs.println(i+","+j+","+(hours[j]-hours[i])+","+(j-i)+","+expected+","+mm[i][j]+","+cm[i][j]+","+pm[i][j]);
        }
      }
    }
    check(!mm[0][45]&&mm[0][46],"Within-segment 45/46 boundary incorrect");
    check(!mm[79][80],"Short gap (<45 hours) allowed");
    check(!mm[79][114],"Across-gap exact 45-hour boundary allowed"); // hour79 -> hour124
    check(!mm[79][115],"Expected installed-jar row-index limitation not reproduced"); // hour79 -> hour125
    check(!mm[159][160],"Expected long-gap over-exclusion not reproduced");
    check(falseAllowed==0&&falseExcluded>0,"Expected conservative mismatch not detected");
    boolean miReject=false,cmiReject=false;
    try{MI m=new MI();configure(m);m.initialise(1,1);m.startAddObservations();m.addObservations(Arrays.copyOfRange(ho,0,80),Arrays.copyOfRange(hn,0,80));m.addObservations(Arrays.copyOfRange(ho,80,n),Arrays.copyOfRange(hn,80,n));m.finaliseAddObservations();}
    catch(RuntimeException e){miReject=e.getMessage().contains("multiple observation sets");}
    try{CMI c=new CMI();configure(c);c.initialise(2,1,1);c.startAddObservations();c.addObservations(Arrays.copyOfRange(direction,0,80),Arrays.copyOfRange(hn,0,80),Arrays.copyOfRange(ho,0,80));c.addObservations(Arrays.copyOfRange(direction,80,n),Arrays.copyOfRange(hn,80,n),Arrays.copyOfRange(ho,80,n));c.finaliseAddObservations();}
    catch(RuntimeException e){cmiReject=e.getMessage().contains("multiple observation sets");}
    check(miReject&&cmiReject,"Multiple-set restriction not reproduced");
    String json=String.format(Locale.ROOT,"{\n  \"synthetic_observations\": %d,\n  \"mi_observations\": %d,\n  \"cmi_direction_observations\": %d,\n  \"cmi_period_observations\": %d,\n  \"k_readback_mi\": \"%s\",\n  \"window_readback_mi\": \"%s\",\n  \"k_readback_cmi\": \"%s\",\n  \"window_readback_cmi\": \"%s\",\n  \"protected_java_fields_verified\": true,\n  \"mi_nats\": %.17g,\n  \"cmi_direction_nats\": %.17g,\n  \"cmi_period_nats\": %.17g,\n  \"direction_dimensions\": [2,1,1],\n  \"tracking_api_mi\": %b,\n  \"tracking_api_cmi\": %b,\n  \"observationSetIndices_field_mi\": %b,\n  \"observationTimePoints_field_mi\": %b,\n  \"observationSetIndices_field_cmi\": %b,\n  \"observationTimePoints_field_cmi\": %b,\n  \"multiple_sets_rejected_mi\": %b,\n  \"multiple_sets_rejected_cmi\": %b,\n  \"neighbour_mask_mismatches_with_elapsed_hours\": %d,\n  \"incorrectly_allowed_pairs\": %d,\n  \"incorrectly_excluded_pairs\": %d,\n  \"exact_45_hour_integration_passed\": false\n}\n",n,mi.getNumObservations(),cmi.getNumObservations(),period.getNumObservations(),mi.getProperty("k"),mi.getProperty("DYN_CORR_EXCL"),cmi.getProperty("k"),cmi.getProperty("DYN_CORR_EXCL"),miValue,cmiValue,periodValue,hasTracking(MI.class),hasTracking(CMI.class),hasField(MI.class,"observationSetIndices"),hasField(MI.class,"observationTimePoints"),hasField(CMI.class,"observationSetIndices"),hasField(CMI.class,"observationTimePoints"),miReject,cmiReject,mismatches,falseAllowed,falseExcluded);
    Files.writeString(out.resolve("java_results.json"),json);System.out.print(json);
  }
}
