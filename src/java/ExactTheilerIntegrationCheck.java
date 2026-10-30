import java.nio.file.*;
import java.io.*;
import java.util.*;
import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.*;

/** Verifies the actual compiled CPU neighbour implementation, not a simulated mask. */
public class ExactTheilerIntegrationCheck {
  static class MI extends MutualInfoCalculatorMultiVariateKraskov1 {
    KdTree tree() throws Exception{ensureKdTreesConstructed();return kdTreeJoint;}
    NearestNeighbourSearcher[] searches() throws Exception{ensureKdTreesConstructed();return new NearestNeighbourSearcher[]{kdTreeJoint,nnSearcherSource,nnSearcherDest};}
    void settings(){check(k==4&&dynCorrExcl&&dynCorrExclTime==45,"MI active settings");}
  }
  static class CMI extends ConditionalMutualInfoCalculatorMultiVariateKraskov1 {
    KdTree tree() throws Exception{ensureKdTreesConstructed();return kdTreeJoint;}
    NearestNeighbourSearcher[] searches() throws Exception{ensureKdTreesConstructed();return new NearestNeighbourSearcher[]{kdTreeJoint,kdTreeVar1Conditional,uniNNSearcherVar1,kdTreeVar2Conditional,uniNNSearcherVar2,nnSearcherConditional};}
    void settings(int d){check(k==4&&dynCorrExcl&&dynCorrExclTime==45&&dimensionsVar1==d&&dimensionsVar2==1&&dimensionsCond==1,"CMI settings/dimensions");}
  }
  static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
  static void config(MI c)throws Exception{c.setProperty("NOISE_LEVEL_TO_ADD","0");c.setProperty("NUM_THREADS","1");c.setProperty("NORMALISE","false");}
  static void config(CMI c){c.setProperty("NOISE_LEVEL_TO_ADD","0");c.setProperty("NUM_THREADS","1");c.setProperty("NORMALISE","false");}
  static boolean[][] masks(KdTree tree,int[] hours,NearestNeighbourSearcher[] searches)throws Exception{
    int n=hours.length;boolean[][] result=new boolean[n][n];
    for(int i=0;i<n;i++){
      tree.findPointsWithinR(i,Double.POSITIVE_INFINITY,45,true,result[i],new int[n+1]);
      int expected=0;
      for(int j=0;j<n;j++){boolean eligible=Math.abs(hours[i]-hours[j])>45;check(result[i][j]==eligible,"Actual tree mask differs from elapsed-hour rule");if(eligible)expected++;}
      for(NearestNeighbourSearcher search:searches)if(search!=null)check(search.countPointsWithinR(i,Double.POSITIVE_INFINITY,45,true)==expected,"Marginal tree exclusion differs from joint");
      PriorityQueue<NeighbourNodeData> neighbours=tree.findKNearestNeighbours(4,i,45);
      check(neighbours.size()==4,"k=4 nearest-neighbour count");
      for(NeighbourNodeData neighbour:neighbours)check(Math.abs(hours[i]-hours[neighbour.sampleIndex])>45,"An in-window point reached actual k-nearest search");
    }
    return result;
  }
  static void arrays(int[] expected,MI mi,CMI period,CMI direction)throws Exception{
    ElapsedHourLoader.verify(expected,mi.getObservationTimePoints(),mi.getObservationSetIndices(),mi.getNumObservations());
    ElapsedHourLoader.verify(expected,period.getObservationTimePoints(),period.getObservationSetIndices(),period.getNumObservations());
    ElapsedHourLoader.verify(expected,direction.getObservationTimePoints(),direction.getObservationSetIndices(),direction.getNumObservations());
  }
  public static void main(String[] args)throws Exception{
    Path out=Path.of(args[0]);Files.createDirectories(out);
    int n=241;int[] hours=new int[n];double[][] ho=new double[n][1],hn=new double[n][1],tp=new double[n][1],dir=new double[n][2];Random random=new Random(20261030);
    for(int i=0;i<n;i++){
      // 0..79,90..169,240..319 and a singleton at 400.
      hours[i]=i<80?i:i<160?i+10:i<240?i+80:400;
      ho[i][0]=random.nextGaussian();hn[i][0]=.7*ho[i][0]+random.nextGaussian();tp[i][0]=random.nextGaussian();double theta=random.nextDouble()*2*Math.PI;dir[i][0]=Math.cos(theta);dir[i][1]=Math.sin(theta);
    }
    MI mi=new MI();config(mi);ElapsedHourLoader.load(mi,hours,ho,hn,4,45);mi.settings();
    CMI period=new CMI();config(period);ElapsedHourLoader.load(period,hours,tp,hn,ho,4,45);period.settings(1);
    CMI direction=new CMI();config(direction);ElapsedHourLoader.load(direction,hours,dir,hn,ho,4,45);direction.settings(2);
    arrays(hours,mi,period,direction);
    double a=mi.computeAverageLocalOfObservations(),b=period.computeAverageLocalOfObservations(),c=direction.computeAverageLocalOfObservations();
    check(Double.isFinite(a)&&Double.isFinite(b)&&Double.isFinite(c),"Nonfinite MI/CMI");
    boolean[][] ma=masks(mi.tree(),hours,mi.searches()),mb=masks(period.tree(),hours,period.searches()),mc=masks(direction.tree(),hours,direction.searches());
    try(PrintWriter indices=new PrintWriter(out.resolve("observation_indices.csv").toFile());PrintWriter pairs=new PrintWriter(out.resolve("pair_eligibility.csv").toFile())){
      indices.println("row,expected_elapsed_hour,mi_time,cmi_period_time,cmi_direction_time,mi_set,cmi_period_set,cmi_direction_set");
      pairs.println("row_i,row_j,elapsed_hours,expected_eligible,mi_eligible,cmi_period_eligible,cmi_direction_eligible");
      for(int i=0;i<n;i++){
        indices.println(i+","+hours[i]+","+mi.getObservationTimePoints()[i]+","+period.getObservationTimePoints()[i]+","+direction.getObservationTimePoints()[i]+","+mi.getObservationSetIndices()[i]+","+period.getObservationSetIndices()[i]+","+direction.getObservationSetIndices()[i]);
        for(int j=i+1;j<n;j++){check(ma[i][j]==mb[i][j]&&ma[i][j]==mc[i][j],"MI/CMI masks differ");pairs.println(i+","+j+","+(hours[j]-hours[i])+","+(hours[j]-hours[i]>45)+","+ma[i][j]+","+mb[i][j]+","+mc[i][j]);}
      }
    }
    for(int delta:new int[]{44,45,46}){
      check(ma[0][delta]==(delta>45),"Continuous boundary failed");
      int target=79+delta,index=Arrays.binarySearch(hours,target);check(index>=0,"Missing boundary target");
      check(ma[79][index]==(delta>45),"Across-gap boundary failed");
    }
    check(ma[159][160],"71-hour long-gap pair must remain eligible");
    // Negative control: different set IDs bypass exclusion across a short gap.
    MI separateMI=new MI();config(separateMI);separateMI.setProperty("k","4");separateMI.setProperty("DYN_CORR_EXCL","45");separateMI.setProperty("TIME_DIFF","0");separateMI.initialise(1,1);separateMI.startAddObservations();
    separateMI.addObservationsTrackObservationIDs(Arrays.copyOfRange(ho,0,80),Arrays.copyOfRange(hn,0,80),0,0);
    separateMI.addObservationsTrackObservationIDs(Arrays.copyOfRange(ho,80,n),Arrays.copyOfRange(hn,80,n),1,90);separateMI.finaliseAddObservations();
    CMI separateCMI=new CMI();config(separateCMI);separateCMI.setProperty("k","4");separateCMI.setProperty("DYN_CORR_EXCL","45");separateCMI.initialise(2,1,1);separateCMI.startAddObservations();
    separateCMI.addObservationsTrackObservationIDs(Arrays.copyOfRange(dir,0,80),Arrays.copyOfRange(hn,0,80),Arrays.copyOfRange(ho,0,80),0,0);
    separateCMI.addObservationsTrackObservationIDs(Arrays.copyOfRange(dir,80,n),Arrays.copyOfRange(hn,80,n),Arrays.copyOfRange(ho,80,n),1,90);separateCMI.finaliseAddObservations();
    boolean[] wrongMI=new boolean[n],wrongCMI=new boolean[n];
    separateMI.tree().findPointsWithinR(79,Double.POSITIVE_INFINITY,45,true,wrongMI,new int[n+1]);
    separateCMI.tree().findPointsWithinR(79,Double.POSITIVE_INFINITY,45,true,wrongCMI,new int[n+1]);
    check(wrongMI[80]&&wrongCMI[80],"Negative control failed: different sets should bypass temporal exclusion");
    // A shuffled-predictor reload must retain the identical temporal metadata.
    double[][] shuffled=new double[n][2];for(int i=0;i<n;i++)shuffled[i]=dir[n-1-i];
    CMI surrogate=new CMI();config(surrogate);ElapsedHourLoader.load(surrogate,hours,shuffled,hn,ho,4,45);
    ElapsedHourLoader.verify(hours,surrogate.getObservationTimePoints(),surrogate.getObservationSetIndices(),surrogate.getNumObservations());
    masks(surrogate.tree(),hours,surrogate.searches());check(Double.isFinite(surrogate.computeAverageLocalOfObservations()),"Surrogate reload failed");
    String result=String.format(Locale.ROOT,"{\n  \"exact_45_hour_integration_passed\": true,\n  \"observations\": %d,\n  \"segments\": 4,\n  \"all_observations_retained\": true,\n  \"all_stored_time_indices_match\": true,\n  \"all_set_ids_zero\": true,\n  \"k\": 4,\n  \"window_hours\": 45,\n  \"boundary_hours_tested\": [44,45,46],\n  \"joint_and_marginal_searches_verified\": true,\n  \"actual_k_nearest_searches_verified\": true,\n  \"unordered_pairs_checked_per_calculator\": %d,\n  \"mismatches\": 0,\n  \"different_set_short_gap_bypass_verified_mi_and_cmi\": true,\n  \"singleton_segment_retained\": true,\n  \"direction_dimensions\": [2,1,1],\n  \"surrogate_reload_timing_verified\": true,\n  \"mi_nats\": %.17g,\n  \"cmi_period_nats\": %.17g,\n  \"cmi_direction_nats\": %.17g\n}\n",n,n*(n-1)/2,a,b,c);
    Files.writeString(out.resolve("java_results.json"),result);System.out.print(result);
  }
}
